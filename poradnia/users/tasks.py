import logging

from celery import shared_task
from django.contrib.sessions.models import Session
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    ignore_result=False,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def clear_expired_sessions(self) -> dict:
    deleted_count, _ = Session.objects.filter(expire_date__lt=timezone.now()).delete()
    logger.info("Cleared %d expired sessions", deleted_count)
    return {"deleted": deleted_count}
