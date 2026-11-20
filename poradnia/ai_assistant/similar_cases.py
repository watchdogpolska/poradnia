"""HTTP client and payload builders for the n8n similar-closed-cases index
webhook (WF I). The contract is frozen; see docs and the n8n workflow before
changing any field name or shape.
"""

import hashlib
import json
import logging

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class IndexWebhookError(Exception):
    """n8n answered 2xx but with ``ok`` not true."""


def sha256_hex(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _scope_flags(scope):
    return {
        "is_dip": scope.is_dip,
        "is_local_government": scope.is_local_government,
        "is_slapp": scope.is_slapp,
    }


def _closed_at(case):
    return case.status_changed.date().isoformat() if case.status_changed else None


def content_hash(text):
    return sha256_hex(text)


def metadata_hash(case):
    advice = case.advice
    data = {
        "institution_kind_id": advice.institution_kind_id,
        "scope_id": advice.scope_id,
        **_scope_flags(advice.scope),
        "closed_at": _closed_at(case),
    }
    return sha256_hex(json.dumps(data, sort_keys=True))


def build_case_metadata(case, text_hash):
    advice = case.advice
    return {
        "id": case.pk,
        "institution_kind_id": advice.institution_kind_id,
        "institution_kind_name": advice.institution_kind.name,
        "scope_id": advice.scope_id,
        "scope_flags": _scope_flags(advice.scope),
        "closed_at": _closed_at(case),
        "content_hash": text_hash,
    }


def post_index(body):
    webhook_url = getattr(settings, "N8N_SIMILAR_CASES_INDEX_WEBHOOK", None)
    webhook_token = getattr(settings, "N8N_SIMILAR_CASES_INDEX_WEBHOOK_TOKEN", None)

    if not webhook_url or not webhook_token:
        raise ImproperlyConfigured(
            "N8N_SIMILAR_CASES_INDEX_WEBHOOK and N8N_SIMILAR_CASES_INDEX_WEBHOOK_TOKEN"
            " must be set."
        )

    response = requests.post(
        webhook_url,
        json=body,
        headers={
            "Authorization": f"Bearer {webhook_token}",
            "Content-Type": "application/json",
        },
        timeout=getattr(settings, "N8N_SIMILAR_CASES_INDEX_WEBHOOK_TIMEOUT", 180),
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or data.get("ok") is not True:
        error = data.get("error") if isinstance(data, dict) else data
        raise IndexWebhookError(f"Index webhook {body['action']} failed: {error}")
    return data


def index_upsert(case, text, reembed):
    text_hash = content_hash(text)
    return post_index(
        {
            "action": "upsert",
            "environment": settings.APP_MODE,
            "reembed": reembed,
            "case": build_case_metadata(case, text_hash),
            "text": text if reembed else None,
        }
    )


def index_delete(case_id):
    return post_index(
        {"action": "delete", "environment": settings.APP_MODE, "case_id": case_id}
    )


def index_reconcile(case_ids):
    # n8n deletes every point whose case_id is not in the list, so an empty
    # list would wipe the whole collection.
    if not case_ids:
        raise ValueError("index_reconcile() refuses an empty case_ids list.")
    return post_index(
        {
            "action": "reconcile",
            "environment": settings.APP_MODE,
            "case_ids": list(case_ids),
        }
    )
