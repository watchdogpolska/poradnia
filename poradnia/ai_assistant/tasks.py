import logging

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from poradnia.cases.models import Case

from . import similar_cases
from .models import SimilarCasesIndexState

logger = logging.getLogger(__name__)

SYNC_MODES = ("incremental", "initial", "reconcile")

_PER_CASE_TASK_OPTIONS = dict(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=False,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)


def _record_sync_error(case_pk, exc):
    state, _ = SimilarCasesIndexState.objects.get_or_create(
        case_id=case_pk, defaults={"status": SimilarCasesIndexState.STATUS_ERROR}
    )
    state.status = SimilarCasesIndexState.STATUS_ERROR
    state.attempts += 1
    state.error = str(exc)[:2000]
    state.save(update_fields=["status", "attempts", "error"])


@shared_task(**_PER_CASE_TASK_OPTIONS)
def sync_case_similar_index_task(self, case_pk):
    """
    Bring one case's entry in the n8n similar-cases index in line with its
    current eligibility, client text and metadata. Idempotent: compares the
    hashes stored in SimilarCasesIndexState and only calls n8n when needed.
    """
    case = (
        Case.objects.eligible_for_similar_cases()
        .select_related("advice__institution_kind", "advice__scope")
        .filter(pk=case_pk)
        .first()
    )
    state = SimilarCasesIndexState.objects.filter(case_id=case_pk).first()
    text = case.get_similar_cases_text() if case else ""

    if case is None or len(text) < settings.SIMILAR_CASES_MIN_TEXT_CHARS:
        if state is None:
            return {"case_pk": case_pk, "action": "skip"}
        try:
            similar_cases.index_delete(case_pk)
        except Exception as exc:
            _record_sync_error(case_pk, exc)
            raise
        state.delete()
        logger.info("Removed case %s from the similar cases index", case_pk)
        return {"case_pk": case_pk, "action": "delete"}

    ch = similar_cases.content_hash(text)
    mh = similar_cases.metadata_hash(case)
    if state and state.content_hash == ch:
        if state.status == SimilarCasesIndexState.STATUS_EMPTY or (
            state.status == SimilarCasesIndexState.STATUS_INDEXED
            and state.metadata_hash == mh
        ):
            return {"case_pk": case_pk, "action": "noop"}

    reembed = (
        state is None
        or state.content_hash != ch
        or state.status
        not in (
            SimilarCasesIndexState.STATUS_INDEXED,
            SimilarCasesIndexState.STATUS_EMPTY,
        )
    )
    try:
        data = similar_cases.index_upsert(case, text, reembed=reembed)
        if not reembed and not data.get("points") and state.points > 0:
            # A metadata-only update matched no points: they were lost in
            # Qdrant, so embed the case again.
            logger.warning(
                "Similar cases index lost the points of case %s; re-embedding",
                case_pk,
            )
            reembed = True
            data = similar_cases.index_upsert(case, text, reembed=True)
    except Exception as exc:
        _record_sync_error(case_pk, exc)
        raise

    points = int(data.get("points") or 0)
    SimilarCasesIndexState.objects.update_or_create(
        case_id=case_pk,
        defaults={
            "content_hash": ch,
            "metadata_hash": mh,
            "points": points,
            "status": (
                SimilarCasesIndexState.STATUS_INDEXED
                if points
                else SimilarCasesIndexState.STATUS_EMPTY
            ),
            "synced_at": timezone.now(),
            "attempts": 0,
            "error": "",
        },
    )
    action = "upsert" if reembed else "metadata"
    logger.info(
        "Similar cases index %s for case %s (points=%s)", action, case_pk, points
    )
    return {"case_pk": case_pk, "action": action}


@shared_task(**_PER_CASE_TASK_OPTIONS)
def delete_case_from_similar_index_task(self, case_pk):
    """
    Remove a deleted case from the n8n similar-cases index. Doesn't read the
    database: the case row is already gone.
    """
    similar_cases.index_delete(case_pk)
    logger.info("Removed deleted case %s from the similar cases index", case_pk)
    return {"case_pk": case_pk, "action": "delete"}


def _enqueue_case_syncs(case_ids, pause_seconds):
    for i, case_pk in enumerate(_highest_first(case_ids)):
        sync_case_similar_index_task.apply_async(
            args=[case_pk], countdown=i * pause_seconds
        )


# Cases are selected (limit) and indexed from the highest case id down.
def _highest_first(ids):
    return sorted(set(ids), reverse=True)


def _narrowed_cases(case_ids, scope_ids):
    cases = Case.objects.all()
    if case_ids:
        cases = cases.filter(pk__in=case_ids)
    if scope_ids:
        cases = cases.filter(advice__scope_id__in=scope_ids)
    return cases


def _initial_case_ids(eligible, limit, force_reembed):
    qs = (
        eligible
        if force_reembed
        else eligible.filter(similar_cases_index_state__isnull=True)
    )
    return list(qs.order_by("-pk").values_list("pk", flat=True)[:limit])


def _incremental_case_ids(cases, eligible, limit, force_check):
    if force_check:
        qs = cases.filter(
            Q(pk__in=eligible.values("pk")) | Q(similar_cases_index_state__isnull=False)
        )
        to_sync = list(qs.order_by("-pk").values_list("pk", flat=True))
        return _highest_first(to_sync)[:limit], len(to_sync), 0

    synced_at = F("similar_cases_index_state__synced_at")
    stale = eligible.filter(
        Q(similar_cases_index_state__isnull=True)
        | Q(modified_on__gt=synced_at)
        | Q(advice__modified_on__gt=synced_at)
        | Q(similar_cases_index_state__status=SimilarCasesIndexState.STATUS_ERROR)
    )
    to_sync = list(stale.order_by("-pk").values_list("pk", flat=True))
    to_delete = list(
        cases.filter(similar_cases_index_state__isnull=False)
        .exclude(pk__in=eligible.values("pk"))
        .order_by("-pk")
        .values_list("pk", flat=True)
    )
    return _highest_first(to_sync + to_delete)[:limit], len(to_sync), len(to_delete)


def _reconcile(eligible, pause_seconds, dry_run):
    case_ids = list(
        eligible.filter(similar_cases_index_state__points__gt=0)
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    result = {"mode": "reconcile", "case_ids": len(case_ids), "dry_run": dry_run}
    if not case_ids:
        # An empty list would make n8n delete every point in the collection.
        logger.info("Similar cases reconcile skipped: no indexed cases")
        return {**result, "skipped": "no_indexed_cases"}
    if dry_run:
        return result

    data = similar_cases.index_reconcile(case_ids)
    known = set(case_ids)
    missing = [pk for pk in data.get("missing") or [] if pk in known]
    orphans_deleted = data.get("orphans_deleted") or []
    SimilarCasesIndexState.objects.filter(case_id__in=missing).delete()
    _enqueue_case_syncs(missing, pause_seconds)
    logger.info(
        "Similar cases reconcile: orphans_deleted=%s missing=%s",
        len(orphans_deleted),
        len(missing),
    )
    return {
        **result,
        "orphans_deleted": len(orphans_deleted),
        "missing": len(missing),
        "enqueued": len(missing),
    }


@shared_task(
    bind=True,
    ignore_result=False,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def sync_similar_cases_index_task(
    self,
    mode="incremental",
    pause_seconds=None,
    limit=None,
    case_ids=None,
    scope_ids=None,
    force_check=False,
    force_reembed=False,
    dry_run=False,
):
    """
    Fan out sync_case_similar_index_task for the cases whose index entry may
    be out of date (initial / incremental), or reconcile Django's list of
    indexed cases with the n8n index (reconcile).

    A no-op while SIMILAR_CASES_INDEX_ENABLED is False, unless case_ids are
    given explicitly (for piloting with the switch off).
    """
    if mode not in SYNC_MODES:
        raise ValueError(f"Unknown similar cases sync mode: {mode!r}")
    if not settings.SIMILAR_CASES_INDEX_ENABLED and not case_ids:
        logger.info("SIMILAR_CASES_INDEX_ENABLED is False; skipping %s sync", mode)
        return {"mode": mode, "skipped": "disabled"}
    if pause_seconds is None:
        pause_seconds = settings.SIMILAR_CASES_SYNC_PAUSE_SECONDS

    cases = _narrowed_cases(case_ids, scope_ids)
    eligible = cases.eligible_for_similar_cases()

    if mode == "reconcile":
        if case_ids or scope_ids or limit:
            # n8n deletes every point outside the list it gets, so reconcile
            # must always see the whole index.
            raise ValueError("reconcile can't be narrowed by case_ids/scope_ids/limit")
        return _reconcile(eligible, pause_seconds, dry_run)

    to_delete = 0
    if mode == "initial":
        ids = _initial_case_ids(eligible, limit, force_reembed)
        to_sync = len(ids)
    else:
        ids, to_sync, to_delete = _incremental_case_ids(
            cases, eligible, limit, force_check
        )

    result = {
        "mode": mode,
        "to_sync": to_sync,
        "to_delete": to_delete,
        "enqueued": 0 if dry_run else len(ids),
        "dry_run": dry_run,
    }
    if dry_run:
        return result

    if mode == "initial" and force_reembed:
        SimilarCasesIndexState.objects.filter(case_id__in=ids).delete()
    _enqueue_case_syncs(ids, pause_seconds)
    logger.info(
        "Similar cases %s sync: enqueued=%s (to_sync=%s, to_delete=%s), %ss apart",
        mode,
        len(ids),
        to_sync,
        to_delete,
        pause_seconds,
    )
    return result


# Delay before a signal-triggered sync runs, so bursts of saves (closing a
# case saves it several times; staff often fix the Advice right after) merge
# into one effective sync. The per-case task is idempotent.
SIGNAL_SYNC_COUNTDOWN = 60


def enqueue_case_sync_on_commit(case_pk):
    transaction.on_commit(
        lambda: sync_case_similar_index_task.apply_async(
            args=[case_pk], countdown=SIGNAL_SYNC_COUNTDOWN
        )
    )


def enqueue_case_delete_on_commit(case_pk):
    transaction.on_commit(
        lambda: delete_case_from_similar_index_task.apply_async(args=[case_pk])
    )


def enqueue_scope_sync_on_commit(scope_pk):
    transaction.on_commit(
        lambda: sync_similar_cases_index_task.delay(
            mode="incremental", scope_ids=[scope_pk], force_check=True
        )
    )
