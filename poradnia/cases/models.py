from django.db import models
from django.contrib.sites.models import Site
from django.conf import settings
from model_utils.fields import MonitorField, StatusField
from model_utils import Choices
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group


class Style(models.Model):
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=30, unique=True)


class Tag(models.Model):
    site = models.ForeignKey(Site)
    style = models.ForeignKey(Style)
    name = models.CharField(max_length=10)


class CaseManager(models.Manager):
    def for_user(self, user):
        queryset = super(CaseManager, self).get_query_set()
        if user.has_perm('cases.can_view_all'):
            return queryset
        field = 'permission__user_id'  # Mam obawy czy to nie jest zbyt wiele relacji...
        return queryset.filter(**{field: user.pk})


class Case(models.Model):
    STATUS = Choices('open', 'closed')
    name = models.CharField(max_length=250)
    tags = models.ManyToManyField(Tag, null=True, blank=True)
    status = StatusField()
    status_changed = MonitorField(monitor='status')
    client = models.ForeignKey(settings.AUTH_USER_MODEL)
    objects = CaseManager()

    def get_absolute_url(self):
        return reverse('cases:detail', kwargs={'pk': str(self.pk)})

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (("can_select_client", "Can select client"),
                       ('can_view_all', "Can view all cases"))


class Permission(models.Model):
    case = models.ForeignKey(Case)
    rank = models.ForeignKey(Group)
