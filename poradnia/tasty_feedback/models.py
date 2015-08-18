from urllib2 import quote
from django.db import models
from model_utils.fields import MonitorField
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.core.mail import mail_managers
from .utils import githubify


class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, help_text=_("Author"), null=True)
    text = models.TextField(verbose_name=_("Comment"),
        help_text=_("Text reported by user"))
    status = models.BooleanField(default=False, verbose_name=_("Status"),
        help_text=_("Feedback has been served"))
    status_changed = MonitorField(monitor='status', verbose_name=_("Status change date"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Creation date"))

    def get_status_display(self):
        return _('open') if self.status else _('closed')

    def __unicode__(self):
        return str(self.created)

    def get_absolute_url(self):
        return reverse("tasty_feedback:details", kwargs={'pk': str(self.pk)})

    def get_github_link(self):
        if hasattr(settings, 'FEEDBACK_GITHUB_REPO'):
            body = quote(githubify(self.text).encode('utf-8'))
            return "%s/issues/new?body=%s" % (settings.FEEDBACK_GITHUB_REPO, body)
        return

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedbacks")


def notify_manager(sender, instance, **kwargs):
    subject = _("New feedback - %(created)s") % instance.__dict__
    message = instance.text
    mail_managers(subject, message)

if getattr(settings, "FEEDBACK_NOTIFY_MANAGERS", True):
    post_save.connect(notify_manager, sender=Feedback, dispatch_uid="notify_manager")
