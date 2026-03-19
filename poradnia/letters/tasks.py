import logging

from celery import shared_task

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
def update_attachment_text_content_task(self, attachment_pk):
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
