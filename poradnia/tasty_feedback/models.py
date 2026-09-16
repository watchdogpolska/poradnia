try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from model_utils.fields import MonitorField

from .utils import githubify


class Feedback(models.Model):
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        help_text=_("Author"),
        null=True,
        on_delete=models.CASCADE,
    )
    url = models.CharField(help_text=_("URL"), max_length=300)
    text = models.TextField(
        verbose_name=_("Content"), help_text=_("Text reported by user")
    )
    status = models.BooleanField(
        default=False, verbose_name=_("Status"), help_text=_("Feedback has been served")
    )
    status_changed = MonitorField(
        monitor="status", verbose_name=_("Status change date")
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Creation date"))

    def get_status_display(self):
        return _("open") if self.status else _("closed")

    def __str__(self):
        return str(self.created)

    def get_absolute_url(self):
        return reverse("tasty_feedback:details", kwargs={"pk": str(self.pk)})

    def get_github_link(self):
        if hasattr(settings, "FEEDBACK_GITHUB_REPO"):
            body = quote(githubify(self.text).encode("utf-8"))
            return "{}/issues/new?body={}".format(settings.FEEDBACK_GITHUB_REPO, body)
        return

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedbacks")
