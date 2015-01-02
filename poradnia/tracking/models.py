from django.db import models
from django.conf import settings
from records.models import Record


class Following(Record):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
