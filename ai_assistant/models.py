import logging

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
        self.environment = environment
        self.status = "pending"
        self.save()

        logger.info("Articles search request accepted: request_id=%s", self.request_id)
        return self.request_id
