from os.path import basename
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from model_utils.fields import MonitorField, StatusField
from model_utils import Choices
from records.models import AbstractRecord


class Letter(AbstractRecord):
    STATUS = Choices(('staff', _('Staff')), ('done', _('Done')))
    GENRE = Choices('mail', 'comment')
    genre = models.CharField(choices=GENRE, default=GENRE.comment, max_length=20)
    status = StatusField()
    status_changed = MonitorField(monitor='status')
    accept = MonitorField(monitor='status', when=['done'], verbose_name=_("Accepted on"))
    name = models.CharField(max_length=250, verbose_name=_("Subject"))
    text = models.TextField(verbose_name=_("Comment"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='letter_created_by', verbose_name=_("Created by"))
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_("Created on"))
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    verbose_name=_("Modified by"),
                                    null=True,
                                    related_name='letter_modified_by')
    modified_on = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name=_("Modified on"))

    def __unicode__(self):
        return self.name

    def get_users(self, force_all=False):
        users_to_notify = self.get_users_with_perms()

        if self.status == self.STATUS.staff or force_all:
            users_to_notify = users_to_notify.filter(is_staff=True)

        return users_to_notify

    def get_absolute_url(self):
        case_url = self.record.case_get_absolute_url()
        return "%s#letter-%s" % (case_url, self.pk)

    def is_done(self):
        return (True if self.status == self.STATUS.done else False)

    def get_edit_url(self):
        return reverse('letters:edit', kwargs={'pk': self.pk})

    def get_send_url(self):
        return reverse('letters:send', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = _('Letter')
        verbose_name_plural = _('Letters')


class Attachment(models.Model):
    letter = models.ForeignKey(Letter)
    attachment = models.FileField(upload_to="letters/%Y/%m/%d")

    @property
    def filename(self):
        return basename(self.attachment.name)

    def __unicode__(self):
        return "%s" % (self.filename)

    def get_absolute_url(self):
        return self.attachment.url

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')
