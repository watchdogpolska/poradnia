from django.db import models
from model_utils.fields import MonitorField
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from urllib2 import quote
from .utils import githubify


class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, help_text=_("Author"))
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
            body = quote(githubify(self.text))
            return "%s/issues/new?body=%s" % (settings.FEEDBACK_GITHUB_REPO, body)
        return

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedbacks")
