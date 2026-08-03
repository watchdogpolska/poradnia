import json
import logging
import uuid

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

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

    def send_tags_request(self):
        """
        Send this case's client messages content and the active tag lists to the
        n8n case-tags webhook.  Intended to be called on an unsaved instance;
        persists it on success.

        Raises ImproperlyConfigured when required settings are absent.
        Raises requests.HTTPError for non-2xx responses.
        """
        from poradnia.advicer.models import Area, InstitutionKind, Issue, PersonKind

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
