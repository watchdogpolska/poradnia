from django.db import models
from django.conf import settings
from cases.models import Case


class Record(models.Model):
    case = models.ForeignKey(Case)
    created_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
