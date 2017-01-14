from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from model_utils.tracker import FieldTracker
from records.models import AbstractRecord, AbstractRecordQuerySet


class Reminder(models.Model):
    event = models.OneToOneField('Event', related_name='user_alarms')
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    triggered = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Reminder')
        verbose_name_plural = _('Reminders')


class Alarm(AbstractRecord):
    event = models.OneToOneField('Event')

    class Meta:
        verbose_name = _('Alarm')
        verbose_name_plural = _('Alarms')


class EventQuerySet(AbstractRecordQuerySet):
    def untriggered(self):
        return self.filter(alarm__isnull=True)

    def old(self):
        return self.filter(time__lte=now())


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
    tracker = FieldTracker(fields=('time',))

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

    def save(self, *args, **kwargs):
        time_changed = self.tracker.has_changed('time')
        super(Event, self).save(*args, **kwargs)

        # if deadline is not set or Event already exists but time was not changed, do nothing
        if not self.deadline or not time_changed:
            return

        # for each staff user involved in case create or update Reminder about Event
        for user in self.case.get_users_with_perms().filter(is_staff=True).exclude(profile=None):
            if user.profile.event_reminder_time > 0:
                Reminder.objects.update_or_create(event=self,
                                                  user=user,
                                                  defaults={'triggered': False})

    @property
    def triggered(self):
        try:
            return bool(self.alarm)
        except Alarm.DoesNotExist:
            return False

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
