import logging

from celery import shared_task

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
def send_old_cases_reminder_task(self) -> None:
    """
    Send reminder emails to users when there are old cases eligible for deletion.
    """
    old_cases_count = Case.objects.old_cases_to_delete().count()

    if old_cases_count <= 0:
        logger.info("No old cases to delete")
        return

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
