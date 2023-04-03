from atom.models import AttachmentBase
from django.conf import settings
from django.db import models
from django.db.models import Case as djCase
from django.db.models import CharField, F, Q, Value, When
from django.db.models.functions import Cast, Concat
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from teryt_tree.dal_ext.filters import AreaMultipleFilter

from poradnia.cases.models import Case
from poradnia.teryt.models import JST
from poradnia.utils.mixins import FormattedDatetimeMixin


class AbstractCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))

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


class AdviceQuerySet(FormattedDatetimeMixin, QuerySet):
    def for_user(self, user):
        if user.has_perm("advicer.can_view_all_advices"):
            return self
        return self.filter(Q(advicer=user.pk) | Q(created_by=user.pk))

    def visible(self):
        return self.filter(visible=True)

    # TODO fix overlap with Advice area property
    def jst_area(self, jst):
        return self.filter(
            jst__tree_id=jst.tree_id, jst__lft__range=(jst.lft, jst.rght)
        )

    # TODO fix overlap with Advice area property
    def area_in(self, jsts):
        if not jsts:
            # Show all results if filter is empty.
            return self
        else:
            return AreaMultipleFilter.filter_area_in(self, jsts, "jst")

    def with_person_kind_name(self):
        return self.annotate(
            person_kind_name=Cast("person_kind__name", output_field=CharField())
        )

    def with_institution_kind_name(self):
        return self.annotate(
            institution_kind_name=Cast(
                "institution_kind__name", output_field=CharField()
            )
        )

    def with_advicer_str(self):
        return self.annotate(
            full_name=Concat(
                F("advicer__first_name"), Value(" "), F("advicer__last_name")
            ),
            advicer_str=djCase(
                When(
                    advicer__is_staff=True,
                    then=Concat(F("full_name"), Value(" (team)")),
                ),
                When(
                    (
                        Q(advicer__first_name__isnull=True)
                        & Q(advicer__last_name__isnull=True)
                    ),
                    then=F("advicer__username"),
                ),
                default=Concat(F("full_name"), Value(" (ext)")),
                output_field=CharField(),
            ),
        )

    def with_helped_str(self):
        return self.annotate(
            helped_str=djCase(
                When(helped=True, then=Value(_("Yes"))),
                When(helped=False, then=Value(_("No"))),
                default=Value("-"),
                output_field=CharField(),
            ),
        )

    def with_visible_str(self):
        return self.annotate(
            visible_str=djCase(
                When(visible=True, then=Value(_("Yes"))),
                When(visible=False, then=Value(_("No"))),
                default=Value("-"),
                output_field=CharField(),
            ),
        )

    def with_jst_name_str(self):
        return self.annotate(
            jst_name=djCase(
                When(jst__name__isnull=False, then=F("jst__name")),
                default=Value("-"),
                output_field=CharField(),
            ),
        )


class Advice(models.Model):
    case = models.OneToOneField(
        to=Case, null=True, blank=True, on_delete=models.CASCADE, verbose_name=_("Case")
    )
    subject = models.CharField(
        max_length=100, verbose_name=_("Subject"), null=True, blank=True
    )
    issues = models.ManyToManyField(
        to=Issue, verbose_name=Issue._meta.verbose_name_plural, blank=True
    )
    area = models.ManyToManyField(
        to=Area, verbose_name=Area._meta.verbose_name_plural, blank=True
    )
    person_kind = models.ForeignKey(
        PersonKind,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=PersonKind._meta.verbose_name,
    )
    institution_kind = models.ForeignKey(
        to=InstitutionKind,
        verbose_name=InstitutionKind._meta.verbose_name,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    advicer = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        verbose_name=_("Advicer"),
        help_text=_("Person who give a advice"),
        limit_choices_to={"is_staff": True},
        on_delete=models.CASCADE,
    )
    grant_on = models.DateTimeField(default=now, verbose_name=_("Grant on"))
    created_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        verbose_name=_("Created by"),
        related_name="advice_created_by",
        on_delete=models.CASCADE,
    )
    created_on = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Creation date")
    )
    helped = models.BooleanField(verbose_name=_("We helped?"), null=True, blank=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        verbose_name=_("Modified by"),
        related_name="advice_modified_by",
        on_delete=models.CASCADE,
    )
    modified_on = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name=_("Modification date")
    )
    visible = models.BooleanField(default=True, verbose_name=_("Visible"))
    comment = models.TextField(verbose_name=_("Comment"), null=True, blank=True)
    jst = models.ForeignKey(
        to=JST,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_("Unit of administrative division"),
        db_index=True,
    )
    objects = AdviceQuerySet.as_manager()

    def __str__(self):
        return self.subject or _("Advice #%d") % (self.pk)

    def get_absolute_url(self):
        return reverse("advicer:detail", kwargs={"pk": self.pk})

    def render_advice_link(self):
        url = self.get_absolute_url()
        label = self.subject
        return f'<a href="{url}">{label}</a>'

    class Meta:
        ordering = ["-created_on"]
        permissions = (("can_view_all_advices", _("Can view all advices")),)
        verbose_name = _("Advice")
        verbose_name_plural = _("Advices")


class Attachment(AttachmentBase):
    advice = models.ForeignKey(to=Advice, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")
