import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from poradnia.advicer import webhook as webhook_module


def _decode_json_response(response):
    return json.loads(response.content.decode("utf-8"))


class WebhookHelpersTestCase(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, body=b"{}", token=None, content_type="application/json"):
        request = self.factory.post("/", data=body, content_type=content_type)
        if token is not None:
            request.headers = {"Authorization": f"Bearer {token}"}
        else:
            request.headers = {}
        return request

    def test_json_error_without_fields(self):
        response = webhook_module._json_error("x", "msg", 418)

        self.assertEqual(response.status_code, 418)
        payload = _decode_json_response(response)
        self.assertEqual(
            payload,
            {
                "status": "error",
                "error": {
                    "code": "x",
                    "message": "msg",
                },
            },
        )

    def test_json_error_with_fields(self):
        response = webhook_module._json_error(
            "validation_error",
            "Invalid payload.",
            400,
            {"subject": ["Required."]},
        )

        self.assertEqual(response.status_code, 400)
        payload = _decode_json_response(response)
        self.assertEqual(payload["error"]["fields"], {"subject": ["Required."]})

    def test_is_int_accepts_int_but_not_bool(self):
        self.assertTrue(webhook_module._is_int(1))
        self.assertTrue(webhook_module._is_int(0))
        self.assertFalse(webhook_module._is_int(True))
        self.assertFalse(webhook_module._is_int(False))
        self.assertFalse(webhook_module._is_int("1"))
        self.assertFalse(webhook_module._is_int(None))

    def test_validate_required_id_list_missing(self):
        errors = {}
        result = webhook_module._validate_required_id_list({}, "issue_ids", errors)

        self.assertEqual(result, [])
        self.assertEqual(errors, {"issue_ids": ["This field is required."]})

    def test_validate_required_id_list_not_a_list(self):
        errors = {}
        result = webhook_module._validate_required_id_list(
            {"issue_ids": "x"}, "issue_ids", errors
        )

        self.assertEqual(result, [])
        self.assertEqual(errors, {"issue_ids": ["Must be a list of integers."]})

    def test_validate_required_id_list_empty(self):
        errors = {}
        result = webhook_module._validate_required_id_list(
            {"issue_ids": []}, "issue_ids", errors
        )

        self.assertEqual(result, [])
        self.assertEqual(errors, {"issue_ids": ["This list may not be empty."]})

    def test_validate_required_id_list_invalid_item(self):
        errors = {}
        result = webhook_module._validate_required_id_list(
            {"issue_ids": [1, "x"]}, "issue_ids", errors
        )

        self.assertEqual(result, [])
        self.assertEqual(errors, {"issue_ids": ["All items must be integers."]})

    def test_validate_required_id_list_ok(self):
        errors = {}
        result = webhook_module._validate_required_id_list(
            {"issue_ids": [1, 2]}, "issue_ids", errors
        )

        self.assertEqual(result, [1, 2])
        self.assertEqual(errors, {})

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="")
    def test_check_token_not_configured(self):
        with patch.dict(os.environ, {}, clear=False):
            request = self._request(token="abc")
            response = webhook_module._check_token(request)

        self.assertEqual(response.status_code, 503)
        payload = _decode_json_response(response)
        self.assertEqual(payload["error"]["code"], "webhook_not_configured")

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="secret")
    def test_check_token_missing_header(self):
        request = self._request(token=None)
        response = webhook_module._check_token(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            _decode_json_response(response)["error"]["message"],
            "Missing bearer token.",
        )

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="secret")
    def test_check_token_invalid(self):
        request = self._request(token="bad")
        response = webhook_module._check_token(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            _decode_json_response(response)["error"]["message"],
            "Invalid bearer token.",
        )

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="")
    def test_check_token_uses_env_fallback(self):
        with patch.dict(os.environ, {"ADVICER_WEBHOOK_BEARER_TOKEN": "env-secret"}):
            request = self._request(token="env-secret")
            response = webhook_module._check_token(request)

        self.assertIsNone(response)

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="secret")
    def test_check_token_valid(self):
        request = self._request(token="secret")
        response = webhook_module._check_token(request)
        self.assertIsNone(response)

    def test_parse_payload_invalid_utf8(self):
        request = self._request(body=b"\xff")
        payload, error = webhook_module._parse_payload(request)

        self.assertIsNone(payload)
        self.assertEqual(error.status_code, 400)
        self.assertEqual(_decode_json_response(error)["error"]["code"], "invalid_json")

    def test_parse_payload_invalid_json(self):
        request = self._request(body=b"{not json}")
        payload, error = webhook_module._parse_payload(request)

        self.assertIsNone(payload)
        self.assertEqual(error.status_code, 400)
        self.assertEqual(_decode_json_response(error)["error"]["code"], "invalid_json")

    def test_parse_payload_non_object(self):
        request = self._request(body=json.dumps([1, 2, 3]).encode("utf-8"))
        payload, error = webhook_module._parse_payload(request)

        self.assertIsNone(payload)
        self.assertEqual(error.status_code, 400)
        self.assertEqual(
            _decode_json_response(error)["error"]["code"], "invalid_payload"
        )

    def test_parse_payload_ok(self):
        request = self._request(body=json.dumps({"x": 1}).encode("utf-8"))
        payload, error = webhook_module._parse_payload(request)

        self.assertEqual(payload, {"x": 1})
        self.assertIsNone(error)

    def test_validate_identifiers_missing_case_id(self):
        errors = {}
        webhook_module._validate_identifiers({}, errors)

        self.assertEqual(errors, {"case_id": ["This field is required."]})

    def test_validate_identifiers_non_int(self):
        errors = {}
        webhook_module._validate_identifiers({"case_id": "1"}, errors)

        self.assertEqual(errors, {"case_id": ["This field must be integer."]})

    def test_validate_identifiers_ok(self):
        errors = {}
        webhook_module._validate_identifiers({"case_id": 1}, errors)

        self.assertEqual(errors, {})

    def test_validate_create_requirements_for_create(self):
        errors = {}
        webhook_module._validate_create_requirements({"case_id": 1}, errors)

        self.assertEqual(
            errors,
            {
                "advicer_id": ["This field is required on create and must be integer."],
                "created_by_id": [
                    "This field is required on create and must be integer."
                ],
            },
        )

    def test_validate_required_fields(self):
        errors = {}
        webhook_module._validate_required_fields({}, errors)

        self.assertEqual(
            errors,
            {
                "subject": ["This field is required and must be string."],
                "institution_kind_id": ["This field is required and must be integer."],
                "person_kind_id": ["This field is required and must be integer."],
                "jst_id": ["This field is required and must be integer."],
            },
        )

    def test_validate_required_fields_blank_subject(self):
        errors = {}
        webhook_module._validate_required_fields(
            {
                "subject": "   ",
                "institution_kind_id": 1,
                "person_kind_id": 2,
                "jst_id": 3,
            },
            errors,
        )

        self.assertEqual(errors, {"subject": ["This field may not be blank."]})

    def test_validate_optional_fields(self):
        errors = {}
        webhook_module._validate_optional_fields(
            {
                "comment": "",
                "helped": "yes",
                "visible": 1,
                "grant_on": "not-a-date",
                "modified_by_id": "x",
            },
            errors,
        )

        self.assertEqual(
            errors,
            {
                "comment": ["Must be a non-empty string."],
                "helped": ["Must be a boolean."],
                "visible": ["Must be a boolean."],
                "grant_on": ["Must be a valid non-empty ISO-8601 datetime string."],
                "modified_by_id": ["Must be an integer."],
            },
        )

    def test_validate_payload_ok(self):
        payload = {
            "case_id": 10,
            "advicer_id": 1,
            "created_by_id": 2,
            "subject": "Subject",
            "institution_kind_id": 3,
            "person_kind_id": 4,
            "jst_id": 5,
            "issue_ids": [1, 2],
            "area_ids": [3],
            "comment": "Ok",
            "helped": True,
            "visible": False,
            "grant_on": "2026-04-22T18:30:00+02:00",
            "modified_by_id": 7,
        }

        errors, issue_ids, area_ids = webhook_module._validate_payload(payload)

        self.assertEqual(errors, {})
        self.assertEqual(issue_ids, [1, 2])
        self.assertEqual(area_ids, [3])

    def test_resolve_fk_missing_key(self):
        errors = {}
        model = MagicMock()

        result = webhook_module._resolve_fk(
            payload={},
            key="x_id",
            attr="x",
            model=model,
            errors=errors,
        )

        self.assertIsNone(result)
        self.assertEqual(errors, {})

    def test_resolve_fk_null_not_allowed(self):
        errors = {}
        model = MagicMock()

        result = webhook_module._resolve_fk(
            payload={"x_id": None},
            key="x_id",
            attr="x",
            model=model,
            errors=errors,
            allow_null=False,
        )

        self.assertIsNone(result)
        self.assertEqual(errors, {"x_id": ["Cannot be null."]})

    def test_resolve_fk_null_allowed(self):
        errors = {}
        model = MagicMock()

        result = webhook_module._resolve_fk(
            payload={"x_id": None},
            key="x_id",
            attr="x",
            model=model,
            errors=errors,
            allow_null=True,
        )

        self.assertIsNone(result)
        self.assertEqual(errors, {})

    def test_resolve_fk_not_found(self):
        errors = {}
        model = MagicMock()
        model.__name__ = "FakeModel"
        model.objects.filter.return_value.first.return_value = None

        result = webhook_module._resolve_fk(
            payload={"x_id": 1},
            key="x_id",
            attr="x",
            model=model,
            errors=errors,
        )

        self.assertIsNone(result)
        self.assertEqual(errors, {"x_id": ["FakeModel not found."]})

    def test_resolve_fk_validator_error(self):
        errors = {}
        obj = SimpleNamespace(pk=1)
        model = MagicMock()
        model.objects.filter.return_value.first.return_value = obj
        model.__name__ = "User"

        result = webhook_module._resolve_fk(
            payload={"x_id": 1},
            key="x_id",
            attr="x",
            model=model,
            errors=errors,
            validator=lambda value: "Bad object.",
        )

        self.assertIsNone(result)
        self.assertEqual(errors, {"x_id": ["Bad object."]})

    def test_resolve_fk_ok(self):
        errors = {}
        obj = SimpleNamespace(pk=1)
        model = MagicMock()
        model.objects.filter.return_value.first.return_value = obj

        result = webhook_module._resolve_fk(
            payload={"x_id": 1},
            key="x_id",
            attr="x",
            model=model,
            errors=errors,
        )

        self.assertEqual(result, ("x", obj))
        self.assertEqual(errors, {})

    def test_validate_advicer(self):
        self.assertEqual(
            webhook_module._validate_advicer(SimpleNamespace(is_staff=False)),
            "Advicer must be staff.",
        )
        self.assertIsNone(
            webhook_module._validate_advicer(SimpleNamespace(is_staff=True))
        )

    @patch.object(webhook_module, "get_user_model")
    @patch.object(webhook_module, "Case")
    @patch.object(webhook_module, "Issue")
    @patch.object(webhook_module, "Area")
    @patch.object(webhook_module, "PersonKind")
    @patch.object(webhook_module, "InstitutionKind")
    @patch.object(webhook_module, "JST")
    def test_resolve_relations_ok(
        self,
        jst_model,
        institution_kind_model,
        person_kind_model,
        area_model,
        issue_model,
        case_model,
        get_user_model,
    ):
        staff_user = SimpleNamespace(pk=11, is_staff=True)
        creator = SimpleNamespace(pk=12)
        modifier = SimpleNamespace(pk=13)
        person_kind = SimpleNamespace(pk=21)
        institution_kind = SimpleNamespace(pk=22)
        jst = SimpleNamespace(pk=23)
        case = SimpleNamespace(pk=24)
        issue_1 = SimpleNamespace(pk=31)
        issue_2 = SimpleNamespace(pk=32)
        area_1 = SimpleNamespace(pk=41)

        user_model = MagicMock()
        get_user_model.return_value = user_model

        def _fk_first(model, value):
            mapping = {
                (user_model, 11): staff_user,
                (user_model, 12): creator,
                (user_model, 13): modifier,
                (person_kind_model, 21): person_kind,
                (institution_kind_model, 22): institution_kind,
                (jst_model, 23): jst,
            }
            return mapping.get((model, value))

        def _make_filter(model):
            manager = MagicMock()

            def filter_side_effect(pk):
                return SimpleNamespace(first=lambda: _fk_first(model, pk))

            manager.filter.side_effect = filter_side_effect
            return manager

        user_model.objects = _make_filter(user_model)
        person_kind_model.objects = _make_filter(person_kind_model)
        institution_kind_model.objects = _make_filter(institution_kind_model)
        jst_model.objects = _make_filter(jst_model)

        case_model.objects.filter.return_value.first.return_value = case
        issue_model.objects.in_bulk.return_value = {31: issue_1, 32: issue_2}
        area_model.objects.in_bulk.return_value = {41: area_1}

        errors = {}
        payload = {
            "case_id": 24,
            "advicer_id": 11,
            "created_by_id": 12,
            "modified_by_id": 13,
            "person_kind_id": 21,
            "institution_kind_id": 22,
            "jst_id": 23,
        }

        resolved = webhook_module._resolve_relations(
            payload=payload,
            issue_ids=[31, 32],
            area_ids=[41],
            errors=errors,
        )

        self.assertEqual(errors, {})
        self.assertEqual(resolved["advicer"], staff_user)
        self.assertEqual(resolved["created_by"], creator)
        self.assertEqual(resolved["modified_by"], modifier)
        self.assertEqual(resolved["person_kind"], person_kind)
        self.assertEqual(resolved["institution_kind"], institution_kind)
        self.assertEqual(resolved["jst"], jst)
        self.assertEqual(resolved["case"], case)
        self.assertEqual(resolved["issues"], [issue_1, issue_2])
        self.assertEqual(resolved["area"], [area_1])

    @patch.object(webhook_module, "get_user_model")
    @patch.object(webhook_module, "Case")
    @patch.object(webhook_module, "Issue")
    @patch.object(webhook_module, "Area")
    @patch.object(webhook_module, "PersonKind")
    @patch.object(webhook_module, "InstitutionKind")
    @patch.object(webhook_module, "JST")
    def test_resolve_relations_invalid(
        self,
        jst_model,
        institution_kind_model,
        person_kind_model,
        area_model,
        issue_model,
        case_model,
        get_user_model,
    ):
        non_staff = SimpleNamespace(pk=11, is_staff=False)

        user_model = MagicMock()
        user_model.__name__ = "User"
        person_kind_model.__name__ = "PersonKind"
        institution_kind_model.__name__ = "InstitutionKind"
        jst_model.__name__ = "JST"

        get_user_model.return_value = user_model

        user_model.objects.filter.side_effect = [
            SimpleNamespace(first=lambda: non_staff),  # advicer_id
            SimpleNamespace(first=lambda: None),  # created_by_id
        ]
        person_kind_model.objects.filter.return_value.first.return_value = None
        institution_kind_model.objects.filter.return_value.first.return_value = None
        jst_model.objects.filter.return_value.first.return_value = None
        case_model.objects.filter.return_value.first.return_value = None
        issue_model.objects.in_bulk.return_value = {1: object()}
        area_model.objects.in_bulk.return_value = {}

        errors = {}
        payload = {
            "case_id": 999,
            "advicer_id": 11,
            "created_by_id": 12,
            "person_kind_id": 21,
            "institution_kind_id": 22,
            "jst_id": 23,
        }

        resolved = webhook_module._resolve_relations(
            payload=payload,
            issue_ids=[1, 2],
            area_ids=[5],
            errors=errors,
        )

        self.assertEqual(resolved, {})
        self.assertEqual(
            errors,
            {
                "advicer_id": ["Advicer must be staff."],
                "created_by_id": ["User not found."],
                "person_kind_id": ["PersonKind not found."],
                "institution_kind_id": ["InstitutionKind not found."],
                "jst_id": ["JST not found."],
                "case_id": ["Case not found."],
                "issue_ids": ["Invalid issue ids."],
                "area_ids": ["Invalid area ids."],
            },
        )

    @patch.object(webhook_module, "Advice")
    def test_get_or_create_advice_by_case_updates_existing(self, advice_model):
        case = SimpleNamespace(pk=10)
        advice_obj = SimpleNamespace(pk=7)
        advice_model.objects.filter.return_value.first.return_value = advice_obj

        advice, created = webhook_module._get_or_create_advice({"case": case})

        self.assertEqual(advice, advice_obj)
        self.assertFalse(created)
        advice_model.objects.filter.assert_called_once_with(case=case)

    @patch.object(webhook_module, "Advice")
    def test_get_or_create_advice_by_case_creates_new(self, advice_model):
        case = SimpleNamespace(pk=10)
        new_advice = object()

        advice_model.objects.filter.return_value.first.return_value = None
        advice_model.return_value = new_advice

        advice, created = webhook_module._get_or_create_advice({"case": case})

        self.assertTrue(created)
        self.assertIs(advice, new_advice)
        advice_model.objects.filter.assert_called_once_with(case=case)
        advice_model.assert_called_once_with(case=case)

    def test_apply_advice_payload(self):
        advice = MagicMock()
        advice.issues = MagicMock()
        advice.area = MagicMock()

        payload = {
            "subject": "  Subject  ",
            "comment": "Comment",
            "helped": True,
            "visible": False,
            "grant_on": "2026-04-22T18:30:00+02:00",
        }
        resolved = {
            "advicer": SimpleNamespace(pk=1),
            "created_by": SimpleNamespace(pk=2),
            "modified_by": SimpleNamespace(pk=3),
            "person_kind": SimpleNamespace(pk=4),
            "institution_kind": SimpleNamespace(pk=5),
            "jst": SimpleNamespace(pk=6),
            "case": SimpleNamespace(pk=7),
            "issues": [SimpleNamespace(pk=8)],
            "area": [SimpleNamespace(pk=9)],
        }

        webhook_module._apply_advice_payload(advice, payload, resolved)

        self.assertEqual(advice.subject, "Subject")
        self.assertEqual(advice.comment, "Comment")
        self.assertTrue(advice.helped)
        self.assertFalse(advice.visible)
        self.assertIsNotNone(advice.grant_on)
        self.assertEqual(advice.advicer.pk, 1)
        self.assertEqual(advice.created_by.pk, 2)
        self.assertEqual(advice.modified_by.pk, 3)
        self.assertEqual(advice.person_kind.pk, 4)
        self.assertEqual(advice.institution_kind.pk, 5)
        self.assertEqual(advice.jst.pk, 6)
        self.assertEqual(advice.case.pk, 7)
        advice.save.assert_called_once_with()
        advice.issues.set.assert_called_once_with(resolved["issues"])
        advice.area.set.assert_called_once_with(resolved["area"])


class AdviceWebhookUpsertViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = webhook_module.AdviceWebhookUpsertView.as_view()

    def _request(self, payload):
        request = self.factory.post(
            "/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        request.headers = {"Authorization": "Bearer secret"}
        return request

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="secret")
    @patch.object(webhook_module, "_parse_payload")
    @patch.object(webhook_module, "_check_token")
    def test_post_returns_token_error_first(self, check_token, parse_payload):
        token_error = webhook_module._json_error("unauthorized", "Invalid", 401)
        check_token.return_value = token_error

        response = self.view(self._request({}))

        self.assertEqual(response.status_code, 401)
        parse_payload.assert_not_called()

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="secret")
    @patch.object(webhook_module, "_validate_payload")
    @patch.object(webhook_module, "_parse_payload")
    @patch.object(webhook_module, "_check_token")
    def test_post_returns_parse_error(
        self, check_token, parse_payload, validate_payload
    ):
        check_token.return_value = None
        parse_error = webhook_module._json_error("invalid_json", "Invalid JSON.", 400)
        parse_payload.return_value = (None, parse_error)

        response = self.view(self._request({}))

        self.assertEqual(response.status_code, 400)
        validate_payload.assert_not_called()

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="secret")
    @patch.object(webhook_module, "_validate_payload")
    @patch.object(webhook_module, "_parse_payload")
    @patch.object(webhook_module, "_check_token")
    def test_post_returns_validation_error(
        self, check_token, parse_payload, validate_payload
    ):
        check_token.return_value = None
        parse_payload.return_value = ({"x": 1}, None)
        validate_payload.return_value = ({"subject": ["Required."]}, [], [])

        response = self.view(self._request({}))

        self.assertEqual(response.status_code, 400)
        payload = _decode_json_response(response)
        self.assertEqual(payload["error"]["code"], "validation_error")
        self.assertEqual(payload["error"]["fields"], {"subject": ["Required."]})

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="secret")
    @patch.object(webhook_module, "_resolve_relations")
    @patch.object(webhook_module, "_validate_payload")
    @patch.object(webhook_module, "_parse_payload")
    @patch.object(webhook_module, "_check_token")
    def test_post_returns_relation_error(
        self,
        check_token,
        parse_payload,
        validate_payload,
        resolve_relations,
    ):
        check_token.return_value = None
        parse_payload.return_value = ({"x": 1}, None)
        errors = {}
        validate_payload.return_value = (errors, [1], [2])

        def fill_errors(*args, **kwargs):
            errors["case_id"] = ["Case not found."]
            return {}

        resolve_relations.side_effect = fill_errors

        response = self.view(self._request({}))

        self.assertEqual(response.status_code, 404)
        payload = _decode_json_response(response)
        self.assertEqual(payload["error"]["code"], "case_not_found")
        self.assertNotIn("fields", payload["error"])

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="secret")
    @patch.object(webhook_module, "_apply_advice_payload")
    @patch.object(webhook_module, "_get_or_create_advice")
    @patch.object(webhook_module, "_resolve_relations")
    @patch.object(webhook_module, "_validate_payload")
    @patch.object(webhook_module, "_parse_payload")
    @patch.object(webhook_module, "_check_token")
    def test_post_created(
        self,
        check_token,
        parse_payload,
        validate_payload,
        resolve_relations,
        get_or_create_advice,
        apply_advice_payload,
    ):
        payload = {"case_id": 10, "subject": "Subject"}
        advice = SimpleNamespace(pk=101, case_id=10)

        check_token.return_value = None
        parse_payload.return_value = (payload, None)
        validate_payload.return_value = ({}, [1], [2])
        resolve_relations.return_value = {"issues": [], "area": []}
        get_or_create_advice.return_value = (advice, True)

        response = self.view(self._request(payload))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            _decode_json_response(response),
            {
                "status": "ok",
                "result": "created",
                "advice_id": 101,
                "case_id": 10,
            },
        )
        apply_advice_payload.assert_called_once_with(
            advice,
            payload,
            {"issues": [], "area": []},
        )
        get_or_create_advice.assert_called_once_with({"issues": [], "area": []})

    @override_settings(ADVICER_WEBHOOK_BEARER_TOKEN="secret")
    @patch.object(webhook_module, "_apply_advice_payload")
    @patch.object(webhook_module, "_get_or_create_advice")
    @patch.object(webhook_module, "_resolve_relations")
    @patch.object(webhook_module, "_validate_payload")
    @patch.object(webhook_module, "_parse_payload")
    @patch.object(webhook_module, "_check_token")
    def test_post_updated(
        self,
        check_token,
        parse_payload,
        validate_payload,
        resolve_relations,
        get_or_create_advice,
        apply_advice_payload,
    ):
        payload = {"case_id": 10, "subject": "Subject"}
        advice = SimpleNamespace(pk=88, case_id=10)

        check_token.return_value = None
        parse_payload.return_value = (payload, None)
        validate_payload.return_value = ({}, [1], [2])
        resolve_relations.return_value = {"issues": [], "area": []}
        get_or_create_advice.return_value = (advice, False)

        response = self.view(self._request(payload))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            _decode_json_response(response),
            {
                "status": "ok",
                "result": "updated",
                "advice_id": 88,
                "case_id": 10,
            },
        )
        apply_advice_payload.assert_called_once_with(
            advice,
            payload,
            {"issues": [], "area": []},
        )
        get_or_create_advice.assert_called_once_with({"issues": [], "area": []})
