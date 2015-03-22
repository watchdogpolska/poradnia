from django.db import models
from django.conf import settings
from cases.models import Case


class Readed(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    case = models.ForeignKey(Case)
    time = models.DateTimeField(auto_now=True)

    @classmethod
    def update(cls, user, case):
        obj, created = cls.objects.get_or_create(user=user, case=case)
        if not created:  # Update old object
            obj.save()
        return obj

    class Meta:
        unique_together = (("user", "case"),)
