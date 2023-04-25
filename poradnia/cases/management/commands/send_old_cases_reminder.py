import logging

from django.core.management import BaseCommand

from poradnia.cases.models import Case
from poradnia.template_mail.utils import TemplateKey
from poradnia.users.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send reminders to delete old cases"

    def handle(self, **options):
        old_cases_count = Case.objects.old_cases_to_delete().count()
        if old_cases_count > 0:
            for user in User.objects.filter(is_superuser=True).all():
                template_key = TemplateKey.CASE_DELETE_OLD
                user.send_template_email(
                    template_key, {"old_cases_count": old_cases_count}
                )
                logger.info(
                    f"Delete old cases ({old_cases_count}) "
                    f"notification sent to user {user.email}"
                )
        else:
            logger.info("No old cases to delete")
