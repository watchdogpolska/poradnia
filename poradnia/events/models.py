from datetime import datetime
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.db.models.query import QuerySet
from records.models import AbstractRecord


class Alarm(AbstractRecord):
    event = models.OneToOneField('Event')

    class Meta:
        verbose_name = _('Alarm')
        verbose_name_plural = _('Alarms')


class EventQuerySet(QuerySet):
    def for_user(self, user):
        if user.has_perm('cases.can_view_all'):
            return self
        from cases.models import Case
        case_list = Case.objects.for_user(user).all()
        return self.filter(case_id__in=case_list)

    def untriggered(self):
        return self.filter(alarm__isnull=True)

    def old(self):
        return self.filter(time__lte=datetime.now())


class Event(AbstractRecord):
    deadline = models.BooleanField(default=False, verbose_name=_("Dead-line"))
    time = models.DateTimeField(verbose_name=_("Time"))
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
    objects = EventQuerySet.as_manager()

    def get_absolute_url(self):
        case_url = self.record.case_get_absolute_url()
        return "%s#event-%s" % (case_url, self.pk)

    def get_edit_url(self):
        return reverse('events:edit', kwargs={'pk': self.pk})

    def get_calendar_url(self):
        return reverse('events:calendar', kwargs={'month': self.time.month, 'year': self.time.year})

    def execute(self):
        obj = Alarm(event=self, case=self.case)
        obj.save()
        return obj

    @property
    def triggered(self):
        try:
            return bool(self.alarm)
        except Alarm.DoesNotExist:
            return False

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
