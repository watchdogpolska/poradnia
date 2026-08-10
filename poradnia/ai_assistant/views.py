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

from .models import N8nArticlesSearchRequest, N8nCaseTagsRequest

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
    m = re.match(r"^-\s+\[(https?://[^\]]+)\]\s*$", line)
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


_ARTICLE_URL_LINE_RE = re.compile(
    r"^-\s+(?:\[.+?\]\(.+?\)|\[https?://[^\]]+\]|https?://\S+)\s*$"
)
_LINKIFY_RE = re.compile(r"(\[[^\[\]]*\]\(https?://[^)]+\)|https?://\S+)")
_MD_LINK_RE = re.compile(r"^\[([^\[\]]*)\]\((https?://[^)]+)\)$")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _has_articles_format(lines):
    return any(_ARTICLE_URL_LINE_RE.match(line) for line in lines)


def _linkify_text(text):
    parts = _LINKIFY_RE.split(text)
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            result.append(_BOLD_RE.sub(r"<strong>\1</strong>", escape(part)))
        else:
            md = _MD_LINK_RE.match(part)
            if md:
                label, url = md.group(1), md.group(2)
                escaped_url = escape(url)
                display = escape(label) if label else escaped_url
                result.append(
                    f'<a href="{escaped_url}" target="_blank" '
                    f'rel="noopener noreferrer">{display}</a>'
                )
            else:
                url = part.rstrip(".,;:!?)]}")
                tail = part[len(url) :]
                escaped_url = escape(url)
                result.append(
                    f'<a href="{escaped_url}" target="_blank" '
                    f'rel="noopener noreferrer">{escaped_url}</a>'
                )
                result.append(escape(tail))
    return "".join(result)


def _format_articles_html(response_text):
    """Convert n8n articles-search response to simple HTML for Letter.html."""
    stripped = (response_text or "").strip().replace("\\n", "\n")
    if not stripped:
        return ""

    non_empty = [ln.strip() for ln in stripped.splitlines() if ln.strip()]

    if _has_articles_format(non_empty):
        title = non_empty[0]
        articles = _parse_articles(non_empty[1:])
        parts = [f"<p><strong>ASYSTENT AI - {escape(title)}</strong></p>"]
        if articles:
            parts.append("<ul>")
            for art in articles:
                parts.extend(_render_article_li(art))
            parts.append("</ul>")
        return "\n".join(parts)

    parts = ["<p><strong>ASYSTENT AI:</strong></p>"]
    for line in non_empty:
        parts.append(f"<p>{_linkify_text(line)}</p>")
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
    """Receive article-search results posted back by n8n.

    Accepts POST requests from n8n containing the outcome of an AI-assisted
    article search initiated via ``N8nArticlesSearchRequest``.  The view:

    1. Authenticates the caller with a bearer token (``_check_token``).
    2. Looks up the pending ``N8nArticlesSearchRequest`` by ``request_id``.
    3. On error: marks the request as *failed* and stores the error message.
    4. On success: marks the request as *completed*, stores the plain-text
       response and the ``is_foi`` flag, then creates an
       ``ai_message_staff`` ``Letter`` on the associated case so advisors
       can see the answer inline in the case timeline.

    Expected JSON payload::

        {
            "request_id": "<uuid>",
            "response":   "<plain-text answer>",    # optional on error
            "is_foi":     "<value>",                # optional
            "error":      "<message>"               # present only on failure
        }

    Returns ``{"ok": true, "result": "completed"|"failed"}`` on success,
    or a JSON error object with an appropriate HTTP status code.
    """

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


def _check_case_tags_token(request):
    configured = getattr(settings, "N8N_CASE_TAGS_CALLBACK_TOKEN", "")
    if not configured:
        logger.error("N8N_CASE_TAGS_CALLBACK_TOKEN is not configured")
        return _json_error("webhook_not_configured", "Token not configured.", 503)

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        logger.warning(
            "Case tags callback: missing bearer token from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return _json_error("unauthorized", "Missing bearer token.", 401)

    token = auth.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, configured):
        logger.warning(
            "Case tags callback: invalid bearer token from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return _json_error("unauthorized", "Invalid bearer token.", 401)

    return None


def _validate_nonempty_string(payload, name):
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        return _json_error("missing_field", f"{name} must be a non-empty string.", 400)
    return None


def _validate_fk_int(payload, name, model):
    value = payload.get(name)
    if not isinstance(value, int):
        return _json_error("missing_field", f"{name} must be an integer.", 400)
    if not model.objects.filter(pk=value).exists():
        return _json_error(
            "invalid_field", f"{model.__name__} {value} does not exist.", 400
        )
    return None


def _validate_int_list(payload, name, model):
    ids = payload.get(name)
    if not isinstance(ids, list) or not ids:
        return _json_error("missing_field", f"{name} must be a non-empty list.", 400)
    if not all(isinstance(i, int) for i in ids):
        return _json_error("missing_field", f"{name} must contain only integers.", 400)
    existing = set(model.objects.filter(pk__in=ids).values_list("pk", flat=True))
    missing = set(ids) - existing
    if missing:
        label = model.__name__ + "s"
        return _json_error(
            "invalid_field", f"{label} do not exist: {sorted(missing)}.", 400
        )
    return None


def _validate_case_tags_payload(payload):
    from poradnia.advicer.models import Area, InstitutionKind, Issue, PersonKind
    from poradnia.teryt.models import JST

    err = _validate_nonempty_string(payload, "subject")
    if err:
        return err

    err = _validate_nonempty_string(payload, "summary")
    if err:
        return err

    err = _validate_fk_int(payload, "institution_kind_id", InstitutionKind)
    if err:
        return err

    err = _validate_fk_int(payload, "person_kind_id", PersonKind)
    if err:
        return err

    jst_id = payload.get("jst_id")
    if jst_id is not None:
        if not isinstance(jst_id, str) or not re.fullmatch(r"\d{2,7}", jst_id):
            return _json_error(
                "invalid_field", "jst_id must be a string of 2–7 digits.", 400
            )
        if not JST.objects.filter(pk=jst_id).exists():
            return _json_error("invalid_field", f"JST {jst_id!r} does not exist.", 400)

    err = _validate_int_list(payload, "issue_ids", Issue)
    if err:
        return err

    return _validate_int_list(payload, "area_ids", Area)


@method_decorator(csrf_exempt, name="dispatch")
class N8nCaseTagsCallbackView(View):
    """Receive the AI-tagging result posted back by n8n after
    N8nCaseTagsRequest.send_tags_request().

    Authentication
    --------------
    Bearer token in the Authorization header, validated against
    ``N8N_CASE_TAGS_CALLBACK_TOKEN``.

    Request body (JSON)
    -------------------
    ``request_id``          - str, matches an existing N8nCaseTagsRequest.
    ``error``               - str (optional).  If present the request is marked
                              failed and no further processing occurs.
    ``subject``             - non-empty str.
    ``summary``             - non-empty str.
    ``institution_kind_id`` - int, must reference an existing InstitutionKind.
    ``person_kind_id``      - int, must reference an existing PersonKind.
    ``jst_id``              - str of 2-7 digits (optional), must reference an existing
                              JST if provided.
    ``issue_ids``           - non-empty list[int], all must reference existing Issues.
    ``area_ids``            - non-empty list[int], all must reference existing Areas.

    On success the view upserts ``Advice.ai_assistant_tags`` on the advice
    linked to the request's case and marks the request as completed.  If no
    ``Advice`` exists for the case yet, one is created with the AI Assistant
    bot as both ``advicer`` and ``created_by``.
    """

    def post(self, request, *args, **kwargs):
        err = _check_case_tags_token(request)
        if err:
            return err

        payload, err = _parse_payload(request)
        if err:
            return err

        request_id = payload.get("request_id")
        if not request_id:
            logger.warning("Case tags callback: missing request_id in payload")
            return _json_error("missing_field", "request_id is required.", 400)

        logger.debug("Case tags callback received for request_id=%s", request_id)

        try:
            tags_request = N8nCaseTagsRequest.objects.select_related("case").get(
                request_id=request_id
            )
        except N8nCaseTagsRequest.DoesNotExist:
            logger.warning("Case tags callback: unknown request_id=%r", request_id)
            return _json_error("not_found", f"No request with id {request_id!r}.", 404)

        error = payload.get("error")

        with transaction.atomic():
            if error:
                tags_request.status = "failed"
                tags_request.response = error
                tags_request.save(update_fields=["response", "status", "updated_at"])
                logger.warning("Case tags request %s failed: %s", request_id, error)
                return JsonResponse({"ok": True, "result": "failed"})

            err = _validate_case_tags_payload(payload)
            if err:
                return err

            ai_tags = {
                "subject": payload["subject"],
                "summary": payload["summary"],
                "institution_kind": payload["institution_kind_id"],
                "person_kind": payload["person_kind_id"],
                "issues": payload["issue_ids"],
                "area": payload["area_ids"],
            }
            jst_id = payload.get("jst_id")
            if jst_id is not None:
                ai_tags["jst"] = jst_id

            tags_request.response = json.dumps(ai_tags, ensure_ascii=False, indent=2)
            tags_request.status = "completed"
            tags_request.save(update_fields=["response", "status", "updated_at"])

            logger.info(
                "Case tags %s completed (case=%s)",
                request_id,
                tags_request.case_id,
            )

            if tags_request.case:
                from poradnia.advicer.models import Advice

                bot = _get_or_create_ai_assistant()
                advice, created = Advice.objects.get_or_create(
                    case=tags_request.case,
                    defaults={"advicer": bot, "created_by": bot},
                )
                advice.ai_assistant_tags = ai_tags
                advice.ai_tags_request = tags_request
                advice.save(update_fields=["ai_assistant_tags", "ai_tags_request"])
                logger.info(
                    "%s ai_assistant_tags for case %s (request_id=%s)",
                    "Created advice with" if created else "Updated",
                    tags_request.case_id,
                    request_id,
                )
            else:
                logger.debug(
                    "Case tags %s: no case attached, skipping advice update",
                    request_id,
                )

        return JsonResponse({"ok": True, "result": "completed"})
