from django.db import models

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _
from cases.models import Case
from notifications import notify


class Record(models.Model):
    STATIC_RELATION = ['letter', 'event', 'alarm']
    case = models.ForeignKey(Case)
    letter = models.OneToOneField('letters.Letter', null=True, blank=True)
    event = models.OneToOneField('events.Event', null=True, blank=True)
    alarm = models.OneToOneField('events.Alarm', null=True, blank=True)

    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(
        null=True,
    )
    related_object = generic.GenericForeignKey('content_type', 'object_id')

    @property  # We use OneToOneField as possible
    def content_object(self):
        for field in self.STATIC_RELATION:
            if getattr(self, field + "_id"):
                return getattr(self, field)
        return self.related_object

    @content_object.setter
    def content_object(self, obj):
        for field in self.STATIC_RELATION:
            if self._meta.get_field_by_name(field)[0].rel.to == obj._meta.model:
                setattr(self, field, obj)
        self.related_object = obj

    def get_users_with_perms(self, *args, **kwargs):
        return Case(pk=self.case_id).get_users_with_perms()

    def case_get_absolute_url(self):
        return Case(pk=self.case_id).get_absolute_url()

    class Meta:
        verbose_name = _('Record')
        verbose_name_plural = _('Records')


class AbstractRecord(models.Model):
    record_general = GenericRelation('Record', related_query_name='record')
    case = models.ForeignKey(Case)

    def show_modifier(self):
        return (self.modified_by_id and self.modified_by_id != self.created_by_id)

    def get_users_with_perms(self, *args, **kwargs):
        return self.case.get_users_with_perms(*args, **kwargs)

    def get_template_list(self):
        return "%s/_%s_list.html" % (self._meta.app_label, self._meta.model_name)

    def send_notification(self, actor, verb):
        for user in self.case.get_users_with_perms().exclude(pk=actor.pk):
            notify.send(actor, target=self, verb=verb, recipient=user)

    def save(self, *args, **kwargs):
        created = True if self.pk is None else False
        super(AbstractRecord, self).save(*args, **kwargs)
        if kwargs.get('commit', True):
            if created:
                record = Record(case=self.case)
                record.content_object = self
                record.save()
            self.case.update_counters()

    def __unicode__(self):
        return _("%(object)s in case #%(case_id)d") %\
            {'object': self._meta.model_name, 'case_id': self.case_id}

    class Meta:
        abstract = True
