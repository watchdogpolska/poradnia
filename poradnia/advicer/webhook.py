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
    At least one identifier is required:
    - ``advice_id``: integer, optional. Existing ``Advice.pk`` to update.
    - ``case_id``: integer, optional. Used as an upsert key through ``Advice.case``.

    Required payload fields:
    - ``subject``: non-empty string
    - ``institution_kind_id``: integer, must reference an existing ``InstitutionKind``
    - ``jst_id``: integer, must reference an existing ``JST``
    - ``issue_ids``: non-empty list[integer], every id must reference an existing ``Issue``
    - ``area_ids``: non-empty list[integer], every id must reference an existing ``Area``

    Create additionally requires:
    - ``advicer_id``: integer, must point to a staff user
    - ``created_by_id``: integer

    Optional fields:
    - ``comment``: string or null
    - ``grant_on``: ISO-8601 datetime string
    - ``modified_by_id``: integer or null
    - ``person_kind_id``: integer or null
    - ``helped``: boolean or null
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
        ``advice_id`` points to a non-existent Advice.
    ``503 Service Unavailable``
        Webhook token is not configured on the server.
    """

    def post(self, request, *args, **kwargs):
        configured_token = getattr(
            settings, "ADVICER_WEBHOOK_BEARER_TOKEN", ""
        ) or os.getenv("ADVICER_WEBHOOK_BEARER_TOKEN", "")
        if not configured_token:
            return _json_error(
                code="webhook_not_configured",
                message="Advice webhook token is not configured.",
                status=503,
            )

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _json_error(
                code="unauthorized",
                message="Missing bearer token.",
                status=401,
            )

        token = auth_header.removeprefix("Bearer ").strip()
        if not token or not hmac.compare_digest(token, configured_token):
            return _json_error(
                code="unauthorized",
                message="Invalid bearer token.",
                status=401,
            )

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _json_error(
                code="invalid_json",
                message="Request body must contain valid JSON.",
                status=400,
            )

        if not isinstance(payload, dict):
            return _json_error(
                code="invalid_payload",
                message="JSON payload must be an object.",
                status=400,
            )

        errors = {}
        advice_id = payload.get("advice_id")
        case_id = payload.get("case_id")

        if advice_id is None and case_id is None:
            errors["non_field_errors"] = [
                "Provide at least one of advice_id or case_id."
            ]
        if advice_id is not None and not _is_int(advice_id):
            errors["advice_id"] = ["Must be an integer."]
        if case_id is not None and not _is_int(case_id):
            errors["case_id"] = ["Must be an integer."]

        if "subject" not in payload:
            errors["subject"] = ["This field is required."]
        else:
            subject = payload["subject"]
            if not isinstance(subject, str):
                errors["subject"] = ["Must be a string."]
            elif not subject.strip():
                errors["subject"] = ["This field may not be blank."]

        if "comment" in payload:
            value = payload["comment"]
            if value is not None and not isinstance(value, str):
                errors["comment"] = ["Must be a string or null."]

        if "grant_on" in payload:
            value = payload["grant_on"]
            if not isinstance(value, str) or parse_datetime(value) is None:
                errors["grant_on"] = ["Must be a valid ISO-8601 datetime string."]

        required_int_fields = ["institution_kind_id", "jst_id"]
        optional_int_fields = [
            "advicer_id",
            "created_by_id",
            "modified_by_id",
            "person_kind_id",
        ]

        for field_name in required_int_fields:
            if field_name not in payload:
                errors[field_name] = ["This field is required."]
            elif not _is_int(payload[field_name]):
                errors[field_name] = ["Must be an integer."]

        for field_name in optional_int_fields:
            if field_name in payload:
                value = payload[field_name]
                if value is not None and not _is_int(value):
                    errors[field_name] = ["Must be an integer or null."]

        if (
            "helped" in payload
            and payload["helped"] is not None
            and not isinstance(payload["helped"], bool)
        ):
            errors["helped"] = ["Must be a boolean or null."]

        if "visible" in payload and not isinstance(payload["visible"], bool):
            errors["visible"] = ["Must be a boolean."]

        issue_ids = _validate_required_id_list(payload, "issue_ids", errors)
        area_ids = _validate_required_id_list(payload, "area_ids", errors)

        if errors:
            return _json_error(
                code="validation_error",
                message="Payload validation failed.",
                status=400,
                fields=errors,
            )

        advice = None
        if advice_id is not None:
            advice = Advice.objects.filter(pk=advice_id).first()
            if advice is None:
                return _json_error(
                    code="advice_not_found",
                    message="Advice not found.",
                    status=404,
                )

        case = None
        if case_id is not None:
            case = Case.objects.filter(pk=case_id).first()
            if case is None:
                errors["case_id"] = ["Case not found."]
            elif advice is not None and advice.case_id not in (None, case.pk):
                errors["case_id"] = ["Does not match the existing advice.case_id."]

        if advice is None and case_id is not None:
            advice = Advice.objects.filter(case_id=case_id).first()

        created = advice is None

        if created:
            if "advicer_id" not in payload:
                errors["advicer_id"] = [
                    "This field is required when creating an Advice."
                ]
            if "created_by_id" not in payload:
                errors["created_by_id"] = [
                    "This field is required when creating an Advice."
                ]
            advice = Advice()

        User = get_user_model()

        resolved_values = {}
        fk_specs = [
            ("advicer_id", "advicer", User, False),
            ("created_by_id", "created_by", User, False),
            ("modified_by_id", "modified_by", User, True),
            ("person_kind_id", "person_kind", PersonKind, True),
            (
                "institution_kind_id",
                "institution_kind",
                InstitutionKind,
                False,
            ),
            ("jst_id", "jst", JST, False),
        ]

        for payload_key, attr_name, model, allow_null in fk_specs:
            if payload_key not in payload:
                continue

            value = payload[payload_key]
            if value is None:
                if allow_null:
                    resolved_values[attr_name] = None
                else:
                    errors[payload_key] = ["This field may not be null."]
                continue

            instance = model.objects.filter(pk=value).first()
            if instance is None:
                errors[payload_key] = [f"{model.__name__} not found."]
                continue

            if payload_key == "advicer_id" and not instance.is_staff:
                errors[payload_key] = ["Advicer must reference a staff user."]
                continue

            resolved_values[attr_name] = instance

        issue_map = Issue.objects.in_bulk(issue_ids)
        missing_issue_ids = sorted(set(issue_ids) - set(issue_map))
        if missing_issue_ids:
            errors["issue_ids"] = [f"Issue ids not found: {missing_issue_ids}"]
        else:
            resolved_values["issues"] = [issue_map[pk] for pk in issue_ids]

        area_map = Area.objects.in_bulk(area_ids)
        missing_area_ids = sorted(set(area_ids) - set(area_map))
        if missing_area_ids:
            errors["area_ids"] = [f"Area ids not found: {missing_area_ids}"]
        else:
            resolved_values["area"] = [area_map[pk] for pk in area_ids]

        if errors:
            return _json_error(
                code="validation_error",
                message="Payload validation failed.",
                status=400,
                fields=errors,
            )

        with transaction.atomic():
            if case_id is not None:
                advice.case = case

            advice.subject = payload["subject"].strip()

            for field_name in ["comment", "helped", "visible"]:
                if field_name in payload:
                    setattr(advice, field_name, payload[field_name])

            if "grant_on" in payload:
                advice.grant_on = parse_datetime(payload["grant_on"])

            for attr_name in [
                "advicer",
                "created_by",
                "modified_by",
                "person_kind",
                "institution_kind",
                "jst",
            ]:
                if attr_name in resolved_values:
                    setattr(advice, attr_name, resolved_values[attr_name])

            if created and "modified_by" not in resolved_values:
                advice.modified_by = resolved_values["created_by"]

            advice.save()
            advice.issues.set(resolved_values["issues"])
            advice.area.set(resolved_values["area"])

        return JsonResponse(
            {
                "status": "ok",
                "result": "created" if created else "updated",
                "advice_id": advice.pk,
                "case_id": advice.case_id,
                "detail_url": advice.get_absolute_url(),
            },
            status=201 if created else 200,
        )
