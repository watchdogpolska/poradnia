from django.db import models
from django.conf import settings
from cases.models import Case


class Tracking(models.Model):
    case = models.ForeignKey(Case)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
