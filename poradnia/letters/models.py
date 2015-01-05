from django.db import models
from model_utils.fields import MonitorField, StatusField
from model_utils import Choices
from records.models import Record
from django.conf import settings


class Letter(Record):
    STATUS = Choices('staff', 'done')
    GENRE = Choices('mail', 'comment')
    status = StatusField()
    genre = models.CharField(choices=GENRE, default=GENRE.mail, max_length=20)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    status_changed = MonitorField(monitor='status')
    accept = MonitorField(monitor='status', when=['done'])
    name = models.CharField(max_length=250)
    text = models.TextField()

    def __unicode__(self):
        return self.name


class Attachment(models.Model):
    letter = models.ForeignKey(Letter)
    attachment = models.FileField(upload_to="letters/%Y/%m/%d")
    text = models.CharField(max_length=150)
