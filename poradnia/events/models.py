from django.db import models
from records.models import AbstractRecord
from django.conf import settings
from django.core.urlresolvers import reverse


class Event(AbstractRecord):
    deadline = models.BooleanField(default=False)
    time = models.DateTimeField()
    for_client = models.BooleanField(default=False)
    text = models.CharField(max_length=150)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='event_created_by')
    created_on = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='event_modified_by')
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)

    def get_absolute_url(self):
        case_url = self.record.case_get_absolute_url()
        return "%s#event-%s" % (case_url, self.pk)

    def get_edit_url(self):
        return reverse('events:edit', kwargs={'pk': self.pk})

    @property
    def triggered(self):
        return bool(self.alarm)


class Alarm(AbstractRecord):
    event = models.OneToOneField(Event)
