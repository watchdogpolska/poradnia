from os.path import basename
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from model_utils.fields import MonitorField, StatusField
from model_utils import Choices
from records.models import AbstractRecord


class Letter(AbstractRecord):
    STATUS = Choices('staff', 'done')
    GENRE = Choices('mail', 'comment')
    status = StatusField()
    genre = models.CharField(choices=GENRE, default=GENRE.mail, max_length=20)
    send_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="senders")
    status_changed = MonitorField(monitor='status')
    accept = MonitorField(monitor='status', when=['done'])
    name = models.CharField(max_length=250)
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="letter_created")
    created_on = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
        related_name="letter_modified")
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)

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

    def get_edit_url(self):
        return reverse('letters:edit', kwargs={'pk': self.pk})

    def get_send_url(self):
        return reverse('letters:send', kwargs={'pk': self.pk})


class Attachment(models.Model):
    letter = models.ForeignKey(Letter)
    attachment = models.FileField(upload_to="letters/%Y/%m/%d")

    @property
    def filename(self):
        return basename(self.attachment.name)

    def __unicode__(self):
        return "%s (%s)" % (self.text, self.filename)

    def get_absolute_url(self):
        return self.attachment.url
