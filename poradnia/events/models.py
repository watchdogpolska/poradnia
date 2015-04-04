from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from records.models import AbstractRecord


class Event(AbstractRecord):
    deadline = models.BooleanField(default=False, verbose_name=_("Dead-line"))
    time = models.DateTimeField(verbose_name=_("Time"))
    for_client = models.BooleanField(
        default=False,
        verbose_name=_("For client"),
        help_text=_("Unchecked are visible for staff only"))
    text = models.CharField(max_length=150, verbose_name=_("Subject"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='event_created_by', verbose_name=_("Created by"))
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_("Created on"))
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    verbose_name=_("Modified by"),
                                    null=True,
                                    related_name='event_modified_by')
    modified_on = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name=_("Modified on"))

    def get_absolute_url(self):
        case_url = self.record.case_get_absolute_url()
        return "%s#event-%s" % (case_url, self.pk)

    def get_edit_url(self):
        return reverse('events:edit', kwargs={'pk': self.pk})

    @property
    def triggered(self):
        return bool(self.alarm)

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')


class Alarm(AbstractRecord):
    event = models.OneToOneField(Event)

    class Meta:
        verbose_name = _('Alarm')
        verbose_name_plural = _('Alarms')
