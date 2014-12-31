from django.db import models
from django.contrib.sites.models import Site
from django.conf import settings
from model_utils.fields import MonitorField, StatusField
from model_utils import Choices


class Style(models.Model):
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=30, unique=True)


class Tag(models.Model):
    site = models.ForeignKey(Site)
    style = models.ForeignKey(Style)
    name = models.CharField(max_length=10)


class Case(models.Model):
    STATUS = Choices('open', 'closed')
    name = models.CharField(max_length=250)
    tags = models.ManyToManyField(Tag)
    status = StatusField()
    status_changed = MonitorField(monitor='status')
    client = models.ForeignKey(settings.AUTH_USER_MODEL)
