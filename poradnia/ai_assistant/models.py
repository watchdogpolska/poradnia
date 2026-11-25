import json
import logging
import uuid

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class N8nArticlesSearchRequest(models.Model):
    request_id = models.CharField(max_length=100, unique=True)
    environment = models.CharField(max_length=10)  # DEV / DEMO / PROD
    question = models.TextField()
    direct_search = models.BooleanField(default=False)
    response = models.TextField(blank=True)
    is_foi = models.CharField(max_length=3, blank=True)  # TAK / NIE
    status = models.CharField(
        max_length=20, default="pending"
    )  # pending / completed / failed
    case = models.ForeignKey(
        "cases.Case",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_search_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    letter = models.OneToOneField(
        "letters.Letter",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_search_request",
        verbose_name=_("Letter"),
    )
    accepted_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="accepted_ai_search_requests",
        verbose_name=_("Accepted by"),
    )
    accepted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Accepted at")
    )
    rejected_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rejected_ai_search_requests",
        verbose_name=_("Rejected by"),
    )
    rejected_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Rejected at")
    )
    rejection_reason = models.TextField(blank=True, verbose_name=_("Rejection reason"))
    phrase_matches = models.JSONField(
        blank=True, null=True, verbose_name=_("Phrase matches")
    )

    class Meta:
        verbose_name = _("Articles search request")
        verbose_name_plural = _("Articles search requests")

    def search_articles(self):
        """
        Send this instance's question to the n8n articles-search webhook and
        update the instance with the acknowledgement (request_id, environment,
        status).  Intended to be called on an unsaved instance; persists it on
        success.

        Raises ImproperlyConfigured when required settings are absent.
        Raises requests.HTTPError for non-2xx responses.
        """
        webhook_url = getattr(settings, "N8N_ARTICLES_SEARCH_WEBHOOK", None)
        webhook_token = getattr(settings, "N8N_ARTICLES_SEARCH_WEBHOOK_TOKEN", None)

        if not webhook_url or not webhook_token:
            raise ImproperlyConfigured(
                "N8N_ARTICLES_SEARCH_WEBHOOK and N8N_ARTICLES_SEARCH_WEBHOOK_TOKEN"
                " must be set."
            )

        environment = settings.APP_MODE

        logger.info(
            "Sending articles search request: question=%r env=%s direct_search=%s",
            self.question[:100],
            environment,
            self.direct_search,
        )

        try:
            response = requests.post(
                webhook_url,
                json={
                    "chatInput": self.question,
                    "environment": environment,
                    "direct_search": self.direct_search,
                },
                headers={
                    "Authorization": f"Bearer {webhook_token}",
                    "Content-Type": "application/json",
                },
                timeout=getattr(settings, "N8N_ARTICLES_SEARCH_WEBHOOK_TIMEOUT", 10),
            )
            response.raise_for_status()
            data = response.json()
            self.request_id = data["request_id"]
            self.status = "pending"
        except requests.RequestException as exc:
            logger.error("Articles search request failed: %s", exc)
            self.request_id = str(uuid.uuid4())
            self.status = "error"

        self.environment = environment
        self.save()

        if self.status == "error":
            return False

        logger.info("Articles search request accepted: request_id=%s", self.request_id)
        return True


class N8nCaseTagsRequest(models.Model):
    request_id = models.CharField(max_length=100, unique=True)
    environment = models.CharField(max_length=10)  # DEV / DEMO / PROD
    question = models.TextField()
    response = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, default="pending"
    )  # pending / completed / failed
    case = models.ForeignKey(
        "cases.Case",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_tags_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="accepted_ai_tags_requests",
        verbose_name=_("Accepted by"),
    )
    accepted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Accepted at")
    )
    rejected_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rejected_ai_tags_requests",
        verbose_name=_("Rejected by"),
    )
    rejected_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Rejected at")
    )
    rejection_reason = models.TextField(blank=True, verbose_name=_("Rejection reason"))

    class Meta:
        verbose_name = _("Case tags request")
        verbose_name_plural = _("Case tags requests")

    def send_tags_request(self):
        """
        Send this case's client messages content and the active tag lists to the
        n8n case-tags webhook.  Intended to be called on an unsaved instance;
        persists it on success.

        Raises ImproperlyConfigured when required settings are absent.
        Raises requests.HTTPError for non-2xx responses.
        """
        from poradnia.advicer.models import (
            Area,
            InstitutionKind,
            Issue,
            PersonKind,
            Scope,
        )

        webhook_url = getattr(settings, "N8N_CASE_TAGS_WEBHOOK", None)
        webhook_token = getattr(settings, "N8N_CASE_TAGS_WEBHOOK_TOKEN", None)

        if not webhook_url or not webhook_token:
            raise ImproperlyConfigured(
                "N8N_CASE_TAGS_WEBHOOK and N8N_CASE_TAGS_WEBHOOK_TOKEN must be set."
            )

        environment = settings.APP_MODE

        logger.info(
            "Sending case tags request: question=%r env=%s",
            self.question[:100],
            environment,
        )

        payload = {
            "question": self.question,
            "environment": environment,
            "scopes_list": json.loads(Scope.active_as_json()),
            "issues_list": json.loads(Issue.active_as_json()),
            "areas_list": json.loads(Area.active_as_json()),
            "personkind_list": json.loads(PersonKind.active_as_json()),
            "institutionkind_list": json.loads(InstitutionKind.active_as_json()),
        }
        headers = {
            "Authorization": f"Bearer {webhook_token}",
            "Content-Type": "application/json",
        }
        # For debugging, you can uncomment the following line to log the payload being
        #    sent to the webhook
        # print(json.dumps(payload, indent=2))
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=getattr(settings, "N8N_CASE_TAGS_WEBHOOK_TIMEOUT", 10),
            )
            response.raise_for_status()
            data = response.json()
            self.request_id = data["request_id"]
            self.status = "pending"
        except requests.RequestException as exc:
            logger.error("Case tags request failed: %s", exc)
            self.request_id = str(uuid.uuid4())
            self.status = "error"

        self.environment = environment
        self.save()

        if self.status == "error":
            return False

        logger.info("Case tags request accepted: request_id=%s", self.request_id)
        return True


class N8nSimilarCasesRequest(models.Model):
    SOURCE_ADVICE = "advice"
    SOURCE_AI_TAGS = "ai_tags"
    SOURCE_CHOICES = (
        (SOURCE_ADVICE, _("Advice")),
        (SOURCE_AI_TAGS, _("AI tags")),
    )

    request_id = models.CharField(max_length=100, unique=True)
    environment = models.CharField(max_length=10)  # DEV / DEMO / PROD
    question = models.TextField()
    response = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, default="pending"
    )  # pending / completed / failed / error
    case = models.ForeignKey(
        "cases.Case",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_similar_cases_requests",
    )
    requested_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requested_ai_similar_cases",
        verbose_name=_("Requested by"),
    )
    institution_kind = models.ForeignKey(
        "advicer.InstitutionKind",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Institution kind"),
    )
    institution_kind_source = models.CharField(
        max_length=10,
        blank=True,
        choices=SOURCE_CHOICES,
        verbose_name=_("Institution kind source"),
    )
    scope = models.ForeignKey(
        "advicer.Scope",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Scope"),
    )
    scope_source = models.CharField(
        max_length=10,
        blank=True,
        choices=SOURCE_CHOICES,
        verbose_name=_("Scope source"),
    )
    similar_cases = models.JSONField(
        blank=True, null=True, verbose_name=_("Similar cases")
    )
    candidates = models.JSONField(blank=True, null=True, verbose_name=_("Candidates"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    letter = models.OneToOneField(
        "letters.Letter",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_similar_cases_request",
        verbose_name=_("Letter"),
    )
    accepted_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="accepted_ai_similar_cases_requests",
        verbose_name=_("Accepted by"),
    )
    accepted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Accepted at")
    )
    rejected_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rejected_ai_similar_cases_requests",
        verbose_name=_("Rejected by"),
    )
    rejected_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Rejected at")
    )
    rejection_reason = models.TextField(blank=True, verbose_name=_("Rejection reason"))

    class Meta:
        verbose_name = _("Similar cases request")
        verbose_name_plural = _("Similar cases requests")

    def build_payload(self, environment):
        scope = self.scope
        return {
            "environment": environment,
            "case_id": self.case_id,
            "client_id": self.case.client_id if self.case_id else None,
            "question": self.question,
            "institution_kind_id": self.institution_kind_id,
            "institution_kind_name": (
                self.institution_kind.name if self.institution_kind_id else None
            ),
            "scope_id": self.scope_id,
            "scope_flags": {
                "is_dip": scope.is_dip,
                "is_local_government": scope.is_local_government,
                "is_slapp": scope.is_slapp,
            },
        }

    def send_request(self):
        """
        Send this instance's question, institution kind and scope flags to the
        n8n similar-cases webhook and update the instance with the
        acknowledgement (request_id, environment, status). Intended to be
        called on an unsaved instance; always persists it.

        Raises ImproperlyConfigured when required settings are absent.
        Returns False when the request could not be delivered.
        """
        webhook_url = getattr(settings, "N8N_SIMILAR_CASES_WEBHOOK", None)
        webhook_token = getattr(settings, "N8N_SIMILAR_CASES_WEBHOOK_TOKEN", None)

        if not webhook_url or not webhook_token:
            raise ImproperlyConfigured(
                "N8N_SIMILAR_CASES_WEBHOOK and N8N_SIMILAR_CASES_WEBHOOK_TOKEN"
                " must be set."
            )

        environment = settings.APP_MODE

        logger.info(
            "Sending similar cases request: case=%s env=%s institution_kind=%s"
            " scope=%s",
            self.case_id,
            environment,
            self.institution_kind_id,
            self.scope_id,
        )

        try:
            response = requests.post(
                webhook_url,
                json=self.build_payload(environment),
                headers={
                    "Authorization": f"Bearer {webhook_token}",
                    "Content-Type": "application/json",
                },
                timeout=getattr(settings, "N8N_SIMILAR_CASES_WEBHOOK_TIMEOUT", 10),
            )
            response.raise_for_status()
            data = response.json()
            self.request_id = data["request_id"]
            self.status = "pending"
        except requests.RequestException as exc:
            logger.error("Similar cases request failed: %s", exc)
            self.request_id = str(uuid.uuid4())
            self.status = "error"

        self.environment = environment
        self.save()

        if self.status == "error":
            return False

        logger.info("Similar cases request accepted: request_id=%s", self.request_id)
        return True


class SimilarCasesIndexState(models.Model):
    """What Django last pushed to the n8n similar-cases index for a case."""

    STATUS_INDEXED = "indexed"
    STATUS_EMPTY = "empty"
    STATUS_ERROR = "error"
    STATUS_CHOICES = (
        (STATUS_INDEXED, _("Indexed")),
        (STATUS_EMPTY, _("Empty")),
        (STATUS_ERROR, _("Error")),
    )

    case = models.OneToOneField(
        "cases.Case",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="similar_cases_index_state",
        verbose_name=_("Case"),
    )
    content_hash = models.CharField(
        max_length=64, blank=True, verbose_name=_("Content hash")
    )
    metadata_hash = models.CharField(
        max_length=64, blank=True, verbose_name=_("Metadata hash")
    )
    points = models.PositiveSmallIntegerField(default=0, verbose_name=_("Points"))
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, verbose_name=_("Status")
    )
    error = models.TextField(blank=True, verbose_name=_("Error"))
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name=_("Attempts"))
    synced_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Synced at"))

    class Meta:
        verbose_name = _("Similar cases index state")
        verbose_name_plural = _("Similar cases index states")

    def __str__(self):
        return f"{self.case_id}: {self.status}"
