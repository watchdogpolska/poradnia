import logging

from allauth.account.signals import password_changed, password_set
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(password_changed)
def clear_flag_on_password_changed(sender, request, user, **kwargs):
    user.must_change_password = False
    user.save(update_fields=["must_change_password"])
    logger.info("Cleared must_change_password flag for user %s", user.username)


@receiver(password_set)
def clear_flag_on_password_set(sender, request, user, **kwargs):
    user.must_change_password = False
    user.save(update_fields=["must_change_password"])
    logger.info("Cleared must_change_password flag for user %s", user.username)
