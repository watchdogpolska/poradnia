import collections
from urllib.parse import quote

from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Create your models here.
from model_utils.models import TimeStampedModel

from poradnia.events.models import Event
from poradnia.judgements.registry import parser_registry
from poradnia.records.models import AbstractRecord


class Court(TimeStampedModel):
    name = models.CharField(max_length=250, verbose_name=_("Court"))
    active = models.BooleanField(default=True, verbose_name=_("Active status"))
    parser_key = models.CharField(
        max_length=25,
        blank=True,
        verbose_name=_("Parser key"),
        help_text=_("Identifier of parser"),
    )

    def get_parser(self):
        return parser_registry.get(self.parser_key, None)()

    @property
    def parser_status(self):
        return self.parser_key in parser_registry

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Court")
        verbose_name_plural = _("Courts")


class CourtCaseQuerySet(models.QuerySet):
    def with_events(self):
        return self.prefetch_related("courtsession_set__event")


class CourtCase(AbstractRecord):
    court = models.ForeignKey(
        to=Court,
        on_delete=models.CASCADE,
        verbose_name=_("Court"),
        null=True,
        blank=True,
    )
    signature = models.CharField(max_length=50, help_text=_("Court signature"))
    created_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courtcase_created_by",
        verbose_name=_("Created by"),
    )
    modified_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Modified by"),
        null=True,
        related_name="courtcase_modified_by",
    )
    objects = CourtCaseQuerySet.as_manager()

    class Meta:
        verbose_name = _("Court case")
        verbose_name_plural = _("Court cases")
        unique_together = [("court", "signature")]

    @property
    def render_court_order_search_link(self):
        qs = quote(self.signature)
        saos_url = f"https://www.saos.org.pl/search?all={ qs }"
        cbosa_url = f"http://orzeczenia.nsa.gov.pl/cbo/find?q=SYGNATURA+[{ qs }]"
        link = f"[<a href={cbosa_url}> CBOSA</a> | <a href={saos_url}>SAOS</a>]"
        return mark_safe(link)


class CourtSession(TimeStampedModel):
    courtcase = models.ForeignKey(
        to=CourtCase, on_delete=models.CASCADE, verbose_name=_("Court case")
    )
    event = models.OneToOneField(
        Event, on_delete=models.CASCADE, verbose_name=_("Event")
    )
    parser_key = models.CharField(max_length=25, verbose_name=_("Parser key"))

    class Meta:
        verbose_name = _("Court session")
        verbose_name_plural = _("Court sessions")


SessionRow = collections.namedtuple(
    "SessionRecord", ["signature", "datetime", "description"]
)
