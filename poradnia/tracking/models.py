from django.db import models
from django.contrib.auth.models import Group
from django.conf import settings
from records.models import Record


class Following(Record):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    rank = models.ForeignKey(Group)
    notify = models.BooleanField(default=True)
