import hmac
import json
import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from poradnia.letters.models import Letter

from .models import N8nArticlesSearchRequest

logger = logging.getLogger(__name__)

AI_ASSISTANT_USERNAME = getattr(settings, "AI_ASSISTANT_USERNAME", "AIAssistant")
AI_ASSISTANT_EMAIL = getattr(settings, "AI_ASSISTANT_EMAIL", "aiassistant@ai.assistant")


def _json_error(code, message, status):
    return JsonResponse(
        {"status": "error", "error": {"code": code, "message": message}},
        status=status,
    )


def _check_token(request):
    configured = getattr(settings, "N8N_ARTICLES_SEARCH_CALLBACK_TOKEN", "")
    if not configured:
        logger.error("N8N_ARTICLES_SEARCH_CALLBACK_TOKEN is not configured")
        return _json_error("webhook_not_configured", "Token not configured.", 503)

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        logger.warning(
            "Articles search callback: missing bearer token from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return _json_error("unauthorized", "Missing bearer token.", 401)

    token = auth.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, configured):
        logger.warning(
            "Articles search callback: invalid bearer token from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return _json_error("unauthorized", "Invalid bearer token.", 401)

    return None


def _parse_payload(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("Articles search callback: invalid JSON body")
        return None, _json_error("invalid_json", "Invalid JSON.", 400)

    if not isinstance(data, dict):
        logger.warning("Articles search callback: payload is not a JSON object")
        return None, _json_error("invalid_payload", "Must be JSON object.", 400)

    return data, None


def _extract_url(line):
    m = re.match(r"^-\s+\[.+?\]\((.+?)\)\s*$", line)
    if m:
        return m.group(1)
    m = re.match(r"^-\s+(https?://\S+)\s*$", line)
    if m:
        return m.group(1)
    return None


def _build_article(url, lines):
    art = {"url": url, "subject": "", "summary": ""}
    for line in lines:
        if line.startswith("**Temat:**"):
            art["subject"] = line[len("**Temat:**") :].strip()
        elif line.startswith("**Podsumowanie:**"):
            art["summary"] = line[len("**Podsumowanie:**") :].strip()
    return art


def _parse_articles(lines):
    segments = []
    current_url = None
    current_lines = []
    for line in lines:
        url = _extract_url(line)
        if url is not None:
            if current_url is not None:
                segments.append((current_url, current_lines))
            current_url = url
            current_lines = []
        elif current_url is not None:
            current_lines.append(line)
    if current_url is not None:
        segments.append((current_url, current_lines))
    return [_build_article(url, seg_lines) for url, seg_lines in segments]


def _render_article_li(art):
    parts = [
        "  <li>",
        (
            f'    <a href="{escape(art["url"])}" target="_blank" '
            + f'rel="noopener noreferrer">{escape(art["url"])}</a>'
        ),
    ]
    if art["subject"]:
        parts.append(f'    <br><strong>Temat:</strong> {escape(art["subject"])}')
    if art["summary"]:
        parts.append(f'    <br><strong>Podsumowanie:</strong> {escape(art["summary"])}')
    parts.append("  </li>")
    return parts


def _format_articles_html(response_text):
    """Convert n8n articles-search response to simple HTML for Letter.html."""
    stripped = (response_text or "").strip()
    if not stripped:
        return ""

    non_empty = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
    title = non_empty[0]
    articles = _parse_articles(non_empty[1:])

    parts = [f"<p><strong>ASYSTENT AI - {escape(title)}</strong></p>"]
    if articles:
        parts.append("<ul>")
        for art in articles:
            parts.extend(_render_article_li(art))
        parts.append("</ul>")
    return "\n".join(parts)


def _get_or_create_ai_assistant():
    User = get_user_model()
    bot, _ = User.objects.get_or_create(
        username=AI_ASSISTANT_USERNAME,
        defaults={"email": AI_ASSISTANT_EMAIL},
    )
    return bot


@method_decorator(csrf_exempt, name="dispatch")
class N8nArticlesSearchCallbackView(View):
    def post(self, request, *args, **kwargs):
        err = _check_token(request)
        if err:
            return err

        payload, err = _parse_payload(request)
        if err:
            return err

        request_id = payload.get("request_id")
        if not request_id:
            logger.warning("Articles search callback: missing request_id in payload")
            return _json_error("missing_field", "request_id is required.", 400)

        logger.debug("Articles search callback received for request_id=%s", request_id)

        try:
            search_request = N8nArticlesSearchRequest.objects.select_related(
                "case"
            ).get(request_id=request_id)
        except N8nArticlesSearchRequest.DoesNotExist:
            logger.warning(
                "Articles search callback: unknown request_id=%r", request_id
            )
            return _json_error("not_found", f"No request with id {request_id!r}.", 404)

        error = payload.get("error")

        with transaction.atomic():
            if error:
                search_request.status = "failed"
                search_request.response = error
                search_request.save(update_fields=["response", "status", "updated_at"])
                logger.warning(
                    "Articles search request %s failed: %s", request_id, error
                )
                return JsonResponse({"ok": True, "result": "failed"})

            response_text = payload.get("response", "")
            response_html = (
                _format_articles_html(response_text) if response_text else ""
            )
            is_foi = payload.get("is_foi", "")
            search_request.response = response_text
            search_request.is_foi = is_foi
            search_request.status = "completed"
            search_request.save(
                update_fields=["response", "is_foi", "status", "updated_at"]
            )
            logger.info(
                "Articles search %s completed (case=%s, is_foi=%r, response_len=%d)",
                request_id,
                search_request.case_id,
                is_foi,
                len(response_text),
            )

            if search_request.case and response_text:
                bot = _get_or_create_ai_assistant()
                question_preview = (search_request.question or "")[:100]
                letter_name = (
                    f"ASYSTENT AI: {question_preview}"
                    if question_preview
                    else "ASYSTENT AI: odpowiedź asystenta"
                )
                Letter.objects.create(
                    case=search_request.case,
                    genre=Letter.GENRE.ai_message_staff,
                    status=Letter.STATUS.staff,
                    name=letter_name[:200],
                    text=response_text,
                    html=response_html,
                    created_by=bot,
                    created_by_is_staff=True,
                )
                logger.info(
                    "Created ai_message_staff letter for case %s (request_id=%s)",
                    search_request.case_id,
                    request_id,
                )
            elif not search_request.case:
                logger.debug(
                    "Articles search %s: no case attached, skipping letter creation",
                    request_id,
                )
            elif not response_text:
                logger.debug(
                    "Articles search %s: empty response, skipping letter creation",
                    request_id,
                )

        return JsonResponse({"ok": True, "result": "completed"})
