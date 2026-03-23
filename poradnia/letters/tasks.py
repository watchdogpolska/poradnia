import logging

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


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
def update_letter_attachments_text_content_task(self, letter_pk):
    """
    Celery entrypoint for updating all attachment text_content for one letter.
    """
    from poradnia.letters.models import Letter

    try:
        letter = Letter.objects.get(pk=letter_pk)
    except Letter.DoesNotExist:
        msg = f"Letter with pk={letter_pk} not found."
        logger.warning(msg)
        return {
            "letter_pk": letter_pk,
            "status": "not_found",
            "message": msg,
            "attachments_total": 0,
            "attachments_updated": 0,
            "attachments_failed": 0,
        }

    return letter.update_attachments_text_content()


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
def update_attachment_text_content_task(
    self,
    attachment_pk,
    enqueued_at_iso=None,
    queue_name=None,
):
    """
    Update text_content for a single Attachment.

    Designed for:
    - parallel execution
    - safe retries
    - isolation (one bad file won't block others)
    """
    from poradnia.letters.models import Attachment

    try:
        attachment = Attachment.objects.select_related("letter").get(pk=attachment_pk)
    except Attachment.DoesNotExist:
        msg = f"Attachment pk={attachment_pk} not found."
        logger.warning(msg)
        return {
            "attachment_pk": attachment_pk,
            "status": "not_found",
            "message": msg,
        }

    logger.info(
        "Processing attachment pk=%s (letter_pk=%s)",
        attachment.pk,
        attachment.letter_id,
    )

    ok = attachment.update_text_content()

    result = {
        "attachment_pk": attachment.pk,
        "letter_pk": attachment.letter_id,
        "status": "ok" if ok else "failed",
    }

    if ok:
        logger.info(
            "Attachment pk=%s updated successfully",
            attachment.pk,
        )
    else:
        logger.warning(
            "Attachment pk=%s update failed",
            attachment.pk,
        )

    return result


@shared_task(bind=True, ignore_result=False)
def enqueue_attachment_text_content_updates(self, max_batch_size=0):
    """
    Periodic task that tops up the attachment text extraction queue only until
    CELERY_QUEUE_READY_WARN is reached.

    Eligible attachments:
    - text_content_update_result IS NULL
    - text_content_update_result = ""

    Ordering:
    - highest id first
    """
    from poradnia.celery_monitor.tasks import rabbit_api
    from poradnia.letters.models import Attachment
    from poradnia.letters.tasks import update_attachment_text_content_task

    lock_key = "enqueue_attachment_text_content_updates_lock"
    lock_ttl = int(getattr(settings, "CELERY_ATTACHMENT_TEXT_ENQUEUE_LOCK_TTL", 240))

    acquired = cache.add(lock_key, "1", timeout=lock_ttl)
    if not acquired:
        msg = "Previous enqueue_attachment_text_content_updates run is still active."
        logger.info(msg)
        return {"status": "locked", "message": msg}

    try:
        vhost = getattr(settings, "CELERY_MONITOR_VHOST", "/")
        queue_name = getattr(
            settings,
            "CELERY_ATTACHMENT_TEXT_CONTENT_QUEUE",
            getattr(settings, "CELERY_TASK_DEFAULT_QUEUE", "celery"),
        )
        queues = rabbit_api(f"api/queues/{vhost}")
        queue_map = {q["name"]: q for q in queues}
        q = queue_map.get(queue_name)
        if not q:
            msg = f"Queue {queue_name!r} not found in vhost {vhost!r}"
            logger.warning(msg)
            return {
                "status": "queue_not_found",
                "queue": queue_name,
                "vhost": vhost,
                "enqueued": 0,
                "message": msg,
            }

        messages_ready = int(q.get("messages_ready", 0))
        if max_batch_size == 0:
            max_batch_size = int(getattr(settings, "CELERY_QUEUE_READY_WARN", 100))
        free_slots = max(max_batch_size - messages_ready, 0)

        logger.info(
            "Attachment enqueue check: queue=%s vhost=%s messages_ready=%s "
            "max_batch_size=%s free_slots=%s",
            queue_name,
            vhost,
            messages_ready,
            max_batch_size,
            free_slots,
        )

        if free_slots <= 0:
            msg = (
                f"Queue '{queue_name}' already at or above threshold: "
                f"messages_ready={messages_ready}, max_batch_size={max_batch_size}"
            )
            logger.info(msg)
            return {
                "status": "queue_full_enough",
                "queue": queue_name,
                "vhost": vhost,
                "messages_ready": messages_ready,
                "max_batch_size": max_batch_size,
                "enqueued": 0,
                "message": msg,
            }

        attachment_ids = list(
            Attachment.objects.exclude(
                text_content_update_result__in=[
                    "File type not supported",
                    "Processed",
                ]
            )
            .order_by("-id")
            .values_list("id", flat=True)[:free_slots]
        )
        if not attachment_ids:
            msg = "No attachments pending text extraction."
            logger.info(msg)
            return {
                "status": "nothing_to_enqueue",
                "queue": queue_name,
                "vhost": vhost,
                "messages_ready": messages_ready,
                "max_batch_size": max_batch_size,
                "enqueued": 0,
                "message": msg,
            }

        for attachment_id in attachment_ids:
            now = timezone.now()
            update_attachment_text_content_task.apply_async(
                args=[attachment_id],
                kwargs={
                    "enqueued_at_iso": now.isoformat(),
                    "queue_name": queue_name,
                },
                queue=queue_name,
            )

        logger.info(
            "Enqueued %s attachment text extraction task(s) to queue=%s. "
            "messages_ready_before=%s max_batch_size=%s",
            len(attachment_ids),
            queue_name,
            messages_ready,
            max_batch_size,
        )

        return {
            "status": "ok",
            "queue": queue_name,
            "vhost": vhost,
            "messages_ready": messages_ready,
            "max_batch_size": max_batch_size,
            "free_slots": free_slots,
            "enqueued": len(attachment_ids),
            "attachment_ids": attachment_ids,
        }

    except Exception as exc:
        logger.exception(
            "Failed to enqueue attachment text extraction tasks: %s",
            exc,
        )
        raise
    finally:
        cache.delete(lock_key)
