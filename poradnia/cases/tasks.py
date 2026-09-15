import logging

from celery import shared_task
from django.db import close_old_connections

from poradnia.cases.models import Case
from poradnia.template_mail.utils import TemplateKey
from poradnia.users.models import User

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    ignore_result=False,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_old_cases_reminder(self) -> None:
    """
    Send reminder emails to users when there are old cases eligible for deletion.
    """
    old_cases_count = Case.objects.old_cases_to_delete().count()

    if old_cases_count <= 0:
        logger.info("No old cases to delete")
        return {"old_cases_count": 0, "sent": [], "failed": []}

    recipients = User.objects.filter(notify_old_cases=True).only("id", "email")
    template_key = TemplateKey.CASE_DELETE_OLD
    sent = []
    failed = []

    for user in recipients.iterator():
        try:
            user.send_template_email(
                template_key,
                {"old_cases_count": old_cases_count},
            )
            logger.info(
                "Delete old cases (%s) notification sent to user %s",
                old_cases_count,
                user.email,
            )
            sent.append(user.email)
        except Exception:
            logger.exception(
                "Failed to send delete old cases notification to user %s",
                user.email,
            )
            failed.append(user.email)

    return {"old_cases_count": old_cases_count, "sent": sent, "failed": failed}


@shared_task(
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
def search_articles_for_case_task(self, case_pk, direct_search=False):
    """
    Celery entrypoint for searching FOI articles for one case.
    """
    close_old_connections()
    try:
        case = Case.objects.get(pk=case_pk)
    except Case.DoesNotExist:
        msg = f"Case with pk={case_pk} not found."
        logger.warning(msg)
        return {
            "case_pk": case_pk,
            "status": "not_found",
            "message": msg,
        }
    finally:
        close_old_connections()

    ok = case.search_articles_for_case(direct_search=direct_search)

    return {
        "case_pk": case.pk,
        "status": "ok" if ok else "failed",
    }


@shared_task(
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
def request_ai_tags_for_case_task(self, case_pk):
    """
    Celery entrypoint for requesting AI tags for one case.
    """
    close_old_connections()
    try:
        case = Case.objects.get(pk=case_pk)
    except Case.DoesNotExist:
        msg = f"Case with pk={case_pk} not found."
        logger.warning(msg)
        return {
            "case_pk": case_pk,
            "status": "not_found",
            "message": msg,
        }
    finally:
        close_old_connections()

    ok = case.request_ai_tags_for_case()

    return {
        "case_pk": case.pk,
        "status": "ok" if ok else "failed",
    }


@shared_task(
    bind=True,
    ignore_result=False,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def enqueue_request_ai_tags_for_cases_task(self, case_ids, pause_seconds=30):
    """
    Fan out request_ai_tags_for_case_task for a list of case ids, staggering
    each enqueue pause_seconds apart via countdown so they don't all hit the
    n8n webhook at once.
    """
    enqueued = []
    for i, case_pk in enumerate(case_ids):
        request_ai_tags_for_case_task.apply_async(
            args=[case_pk], countdown=i * pause_seconds
        )
        enqueued.append(case_pk)

    logger.info(
        "Enqueued %s request_ai_tags_for_case_task(s), staggered %ss apart.",
        len(enqueued),
        pause_seconds,
    )

    return {"case_ids": enqueued, "enqueued": len(enqueued)}
