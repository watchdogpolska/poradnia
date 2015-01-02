from django.db import models
from django.conf import settings
from cases.models import Case


class Record(models.Model):
    case = models.ForeignKey(Case)
    created_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)

    def get_absolute_url(self):
        return "%s#%d" % (self.case.get_absolute_url(), self.pk)

    def get_child_name(self):
        fields = ('letter', 'event', 'alarm', 'following')  # How to write it better?
        for field in fields:
            if hasattr(self, field):
                return field
        return None

    def get_child_obj(self):
        return getattr(self, self.get_child_name())

    def get_template_list(self):
        return "%s/_%s_list.html" % (self._meta.app_label, self._meta.model_name)
