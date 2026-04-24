import hmac
import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from poradnia.cases.models import Case
from poradnia.teryt.models import JST

from .models import Advice, Area, InstitutionKind, Issue, PersonKind


def _json_error(code, message, status, fields=None):
    payload = {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
        },
    }
    if fields:
        payload["error"]["fields"] = fields
    return JsonResponse(payload, status=status)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_required_id_list(payload, field_name, errors):
    if field_name not in payload:
        errors[field_name] = ["This field is required."]
        return []

    value = payload[field_name]
    if not isinstance(value, list):
        errors[field_name] = ["Must be a list of integers."]
        return []

    if not value:
        errors[field_name] = ["This list may not be empty."]
        return []

    invalid = [item for item in value if not _is_int(item)]
    if invalid:
        errors[field_name] = ["All items must be integers."]
        return []

    return value


def _check_token(request):
    configured = getattr(settings, "ADVICER_WEBHOOK_BEARER_TOKEN", "") or os.getenv(
        "ADVICER_WEBHOOK_BEARER_TOKEN", ""
    )
    if not configured:
        return _json_error("webhook_not_configured", "Token not configured.", 503)

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return _json_error("unauthorized", "Missing bearer token.", 401)

    token = auth.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, configured):
        return _json_error("unauthorized", "Invalid bearer token.", 401)

    return None


def _parse_payload(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, _json_error("invalid_json", "Invalid JSON.", 400)

    if not isinstance(data, dict):
        return None, _json_error("invalid_payload", "Must be JSON object.", 400)

    return data, None


def _validate_identifiers(payload, errors):
    if "case_id" not in payload:
        errors["case_id"] = ["This field is required."]
    elif not _is_int(payload["case_id"]):
        errors["case_id"] = ["This field must be integer."]


def _validate_create_requirements(payload, errors):
    for field in ["advicer_id", "created_by_id"]:
        if field not in payload or not _is_int(payload[field]):
            errors[field] = ["This field is required on create and must be integer."]


def _validate_required_fields(payload, errors):
    if "subject" not in payload or not isinstance(payload["subject"], str):
        errors["subject"] = ["This field is required and must be string."]
    elif not payload["subject"].strip():
        errors["subject"] = ["This field may not be blank."]

    for field in ["institution_kind_id", "person_kind_id", "jst_id"]:
        if field not in payload or not _is_int(payload[field]):
            errors[field] = ["This field is required and must be integer."]


def _validate_optional_fields(payload, errors):
    if "comment" in payload and (
        payload["comment"] is None
        or not isinstance(payload["comment"], str)
        or not payload["comment"].strip()
    ):
        errors["comment"] = ["Must be a non-empty string."]

    if "helped" in payload and (
        payload["helped"] is None or not isinstance(payload["helped"], bool)
    ):
        errors["helped"] = ["Must be a boolean."]

    if "visible" in payload and (
        payload["visible"] is None or not isinstance(payload["visible"], bool)
    ):
        errors["visible"] = ["Must be a boolean."]

    if "grant_on" in payload and (
        not payload["grant_on"]
        or not isinstance(payload["grant_on"], str)
        or not parse_datetime(payload["grant_on"])
    ):
        errors["grant_on"] = ["Must be a valid non-empty ISO-8601 datetime string."]

    if "modified_by_id" in payload and not _is_int(payload["modified_by_id"]):
        errors["modified_by_id"] = ["Must be an integer."]


def _validate_payload(payload):
    errors = {}

    _validate_identifiers(payload, errors)
    _validate_create_requirements(payload, errors)
    _validate_required_fields(payload, errors)
    _validate_optional_fields(payload, errors)

    issue_ids = _validate_required_id_list(payload, "issue_ids", errors)
    area_ids = _validate_required_id_list(payload, "area_ids", errors)

    return errors, issue_ids, area_ids


def _resolve_fk(payload, key, attr, model, errors, allow_null=False, validator=None):
    if key not in payload:
        return None

    val = payload[key]
    if val is None:
        if not allow_null:
            errors[key] = ["Cannot be null."]
        return None

    obj = model.objects.filter(pk=val).first()
    if not obj:
        errors[key] = [f"{model.__name__} not found."]
        return None

    if validator is not None:
        validation_error = validator(obj)
        if validation_error:
            errors[key] = [validation_error]
            return None

    return attr, obj


def _validate_advicer(user):
    if not user.is_staff:
        return "Advicer must be staff."
    return None


def _resolve_relations(payload, issue_ids, area_ids, errors):
    resolved = {}
    User = get_user_model()

    fk_map = [
        ("advicer_id", "advicer", User, False, _validate_advicer),
        ("created_by_id", "created_by", User, False, None),
        ("modified_by_id", "modified_by", User, True, None),
        ("person_kind_id", "person_kind", PersonKind, False, None),
        ("institution_kind_id", "institution_kind", InstitutionKind, False, None),
        ("jst_id", "jst", JST, False, None),
    ]

    for key, attr, model, allow_null, validator in fk_map:
        result = _resolve_fk(
            payload=payload,
            key=key,
            attr=attr,
            model=model,
            errors=errors,
            allow_null=allow_null,
            validator=validator,
        )
        if result:
            attr, obj = result
            resolved[attr] = obj

    if "case_id" in payload:
        case = Case.objects.filter(pk=payload["case_id"]).first()
        if not case:
            errors["case_id"] = ["Case not found."]
        else:
            resolved["case"] = case

    issue_map = Issue.objects.in_bulk(issue_ids)
    if set(issue_ids) != set(issue_map):
        errors["issue_ids"] = ["Invalid issue ids."]
    else:
        resolved["issues"] = list(issue_map.values())

    area_map = Area.objects.in_bulk(area_ids)
    if set(area_ids) != set(area_map):
        errors["area_ids"] = ["Invalid area ids."]
    else:
        resolved["area"] = list(area_map.values())

    return resolved


def _get_or_create_advice(resolved):
    advice = Advice.objects.filter(case=resolved["case"]).first()
    if advice:
        return advice, False

    advice = Advice(case=resolved.get("case"))
    return advice, True


def _apply_advice_payload(advice, payload, resolved):
    advice.subject = payload["subject"].strip()

    for f in ["comment", "helped", "visible"]:
        if f in payload:
            setattr(advice, f, payload[f])

    if "grant_on" in payload:
        advice.grant_on = parse_datetime(payload["grant_on"])

    for attr, val in resolved.items():
        if attr not in ("issues", "area"):
            setattr(advice, attr, val)

    advice.save()
    advice.issues.set(resolved["issues"])
    advice.area.set(resolved["area"])


@method_decorator(csrf_exempt, name="dispatch")
class AdviceWebhookUpsertView(View):
    """
    Bearer-token protected webhook that creates or updates an ``Advice`` record.

    Request
    -------
    Method: ``POST``
    Content-Type: ``application/json``
    Authorization: ``Bearer <ADVICER_WEBHOOK_BEARER_TOKEN>``

    JSON schema
    -----------
    Identifier required for upsert operation:
    - ``case_id``: integer. Existing ``Advice`` is updated by ``Advice.case``;
                   otherwise a new ``Advice`` is created for this case.

    Required payload fields:
    - ``subject``: non-empty string
    - ``institution_kind_id``: integer, must reference an existing ``InstitutionKind``
    - ``person_kind_id``: integer, must reference an existing ``PersonKind``
    - ``jst_id``: integer, must reference an existing ``JST``
    - ``issue_ids``: non-empty list[integer], every id must reference
                     an existing ``Issue``
    - ``area_ids``: non-empty list[integer], every id must reference
                    an existing ``Area``

    Create additionally requires:
    - ``advicer_id``: integer, must point to a staff user
    - ``created_by_id``: integer

    Optional fields:
    - ``comment``: string
    - ``grant_on``: ISO-8601 datetime string
    - ``modified_by_id``: integer
    - ``helped``: boolean
    - ``visible``: boolean

    Example payload
    ---------------
    {
      "case_id": 123,
      "subject": "DIP - urząd nie odpowiada",
      "comment": "Webhook upsert from assistant",
      "advicer_id": 7,
      "created_by_id": 7,
      "modified_by_id": 7,
      "grant_on": "2026-04-22T18:30:00+02:00",
      "person_kind_id": 2,
      "institution_kind_id": 4,
      "helped": true,
      "visible": true,
      "jst_id": 15,
      "issue_ids": [1, 4],
      "area_ids": [2]
    }

    Responses
    ---------
    ``201 Created``
        Advice was created.
    ``200 OK``
        Advice was updated.
    ``400 Bad Request``
        Invalid JSON or schema validation error. Response body contains
        ``error.code`` and optional ``error.fields``.
    ``401 Unauthorized``
        Missing or invalid bearer token.
    ``404 Not Found``
        ``case_id`` points to a non-existent Case.
    ``503 Service Unavailable``
        Webhook token is not configured on the server.
    """

    def post(self, request, *args, **kwargs):
        err = _check_token(request)
        if err:
            return err

        payload, err = _parse_payload(request)
        if err:
            return err

        errors, issue_ids, area_ids = _validate_payload(payload)
        if errors:
            return _json_error("validation_error", "Invalid payload.", 400, errors)

        resolved = _resolve_relations(payload, issue_ids, area_ids, errors)
        if "case_id" in errors and errors["case_id"] == ["Case not found."]:
            return _json_error("case_not_found", "Case not found.", 404)
        if errors:
            return _json_error("validation_error", "Invalid relations.", 400, errors)

        advice, created = _get_or_create_advice(resolved)
        if isinstance(created, JsonResponse):
            return created

        with transaction.atomic():
            _apply_advice_payload(advice, payload, resolved)

        return JsonResponse(
            {
                "status": "ok",
                "result": "created" if created else "updated",
                "advice_id": advice.pk,
                "case_id": advice.case_id,
            },
            status=201 if created else 200,
        )
