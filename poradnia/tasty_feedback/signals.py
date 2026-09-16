from django.conf import settings
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

from .models import Feedback
from .utils import mail_managers_replyable


def notify_manager(sender, instance, **kwargs):
    subject = _("New feedback - %(created)s") % instance.__dict__
    if instance.user:
        user_info = f"{instance.user} <{instance.user.email}>"
    else:
        user_info = _("Anonymous")
    message = f"{instance.text}\nURL:{instance.url}\nUser:{user_info}"
    reply_email = instance.user.email if instance.user else None
    mail_managers_replyable(subject, message, reply_email=reply_email)


if getattr(settings, "FEEDBACK_NOTIFY_MANAGERS", True):
    post_save.connect(notify_manager, sender=Feedback, dispatch_uid="notify_manager")
