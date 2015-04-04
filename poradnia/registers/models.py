import datetime
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _


class AbstractCategory(models.Model):
    name = models.CharField(max_length=50, verbose_name=("Name"))

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class Issue(AbstractCategory):
    pass


class Area(AbstractCategory):
    pass


class PersonKind(AbstractCategory):
    pass


class InstitutionKind(AbstractCategory):
    pass


class AdviceQuerySet(QuerySet):
    def for_user(self, user):
        if user.has_perm('registers.can_view_all_advices'):
            return self
        return self.filter(Q(advicer=user.pk) | Q(created_by=user.pk))

    def visible(self):
        return self.filter(visible=True)


class Advice(models.Model):
    subject = models.CharField(max_length=50, verbose_name=_("Subject"), null=True, blank=True)
    issues = models.ManyToManyField(Issue, null=True, verbose_name=_("Issues"), blank=True)
    area = models.ForeignKey(Area, null=True, verbose_name=_("Area"), blank=True)
    person_kind = models.ForeignKey(PersonKind,
        null=True, blank=True,
        verbose_name=_("Kind of person "))
    institution_kind = models.ForeignKey(InstitutionKind,
        verbose_name=_("Kind of institution"),
        null=True, blank=True)
    advicer = models.ForeignKey(settings.AUTH_USER_MODEL,
        verbose_name=_("Advicer"), help_text=_("Person who give a advice"),
        limit_choices_to={'is_staff': True})
    grant_on = models.DateTimeField(default=datetime.datetime.now, verbose_name=_("Grant on"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
        verbose_name=_("Created by"), related_name='advice_created_by')
    created_on = models.DateTimeField(auto_now_add=True,
        verbose_name=_("Created on"))
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        verbose_name=_("Modified by"),
        related_name='advice_modified_by')
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True,
        verbose_name=_("Modified on"))
    visible = models.BooleanField(default=True, verbose_name=_("Visible"))
    comment = models.TextField(verbose_name=_("Comment"))
    objects = AdviceQuerySet.as_manager()

    def __unicode__(self):
        return self.subject or _("Advice #%d") % (self.pk)

    def get_absolute_url(self):
        return reverse('registers:detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['created_on', ]
        permissions = (('can_view_all_advices', _("Can view all advices"),),
                       )
