from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from atom.models import AttachmentBase
from poradnia.cases.models import Case


@python_2_unicode_compatible
class AbstractCategory(models.Model):
    name = models.CharField(max_length=100,
                            verbose_name=_("Name"))

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Issue(AbstractCategory):
    class Meta:
        verbose_name = _("The thematic scope of the request")
        verbose_name_plural = _("Thematic scopes of requests")


class Area(AbstractCategory):
    class Meta:
        verbose_name = _("Problem regarding the right to information")
        verbose_name_plural = _("Problems regarding the right to information")


class PersonKind(AbstractCategory):
    class Meta:
        verbose_name = _("Type of person who reporting the advice")
        verbose_name_plural = _("Types of people who report to for advice")


class InstitutionKind(AbstractCategory):
    class Meta:
        verbose_name = _("Institution kind")
        verbose_name_plural = _("Institution kinds")


class AdviceQuerySet(QuerySet):
    def for_user(self, user):
        if user.has_perm('advicer.can_view_all_advices'):
            return self
        return self.filter(Q(advicer=user.pk) | Q(created_by=user.pk))

    def visible(self):
        return self.filter(visible=True)


@python_2_unicode_compatible
class Advice(models.Model):
    case = models.OneToOneField(Case,
                                null=True,
                                blank=True,
                                verbose_name=_("Case"))
    subject = models.CharField(max_length=50,
                               verbose_name=_("Subject"),
                               null=True,
                               blank=True)
    issues = models.ManyToManyField(Issue,
                                    verbose_name=Issue._meta.verbose_name_plural,
                                    blank=True)
    area = models.ForeignKey(Area,
                             null=True,
                             verbose_name=Area._meta.verbose_name,
                             blank=True)
    person_kind = models.ForeignKey(PersonKind,
                                    null=True,
                                    blank=True,
                                    verbose_name=PersonKind._meta.verbose_name)
    institution_kind = models.ForeignKey(InstitutionKind,
                                         verbose_name=InstitutionKind._meta.verbose_name,
                                         null=True,
                                         blank=True)
    advicer = models.ForeignKey(settings.AUTH_USER_MODEL,
                                verbose_name=_("Advicer"),
                                help_text=_("Person who give a advice"),
                                limit_choices_to={'is_staff': True})
    grant_on = models.DateTimeField(default=now,
                                    verbose_name=_("Grant on"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   verbose_name=_("Created by"),
                                   related_name='advice_created_by')
    created_on = models.DateTimeField(auto_now_add=True,
                                      verbose_name=_("Creation date"))
    helped = models.NullBooleanField(verbose_name=_("We helped?"),
                                     blank=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    null=True,
                                    verbose_name=_("Modified by"),
                                    related_name='advice_modified_by')
    modified_on = models.DateTimeField(auto_now=True,
                                       null=True,
                                       blank=True,
                                       verbose_name=_("Modification date"))
    visible = models.BooleanField(default=True,
                                  verbose_name=_("Visible"))
    comment = models.TextField(verbose_name=_("Comment"),
                               null=True,
                               blank=True)
    objects = AdviceQuerySet.as_manager()

    def __str__(self):
        return self.subject or _("Advice #%d") % (self.pk)

    def get_absolute_url(self):
        return reverse('advicer:detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['created_on', ]
        permissions = (('can_view_all_advices', _("Can view all advices"),),
                       )
        verbose_name = _("Advice")
        verbose_name_plural = _("Advices")


class Attachment(AttachmentBase):
    advice = models.ForeignKey(Advice)

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")
