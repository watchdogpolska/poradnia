import json
from datetime import timedelta
from io import BytesIO, StringIO
from unittest.mock import MagicMock, call, patch

import openpyxl
import requests as requests_lib
from django.contrib import admin as django_admin
from django.core.exceptions import ImproperlyConfigured
from django.core.management import CommandError, call_command
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from poradnia.advicer.factories import (
    AdviceFactory,
    InstitutionKindFactory,
    ScopeFactory,
)
from poradnia.ai_assistant import similar_cases
from poradnia.ai_assistant import views as views_module
from poradnia.ai_assistant.admin import N8nSimilarCasesRequestAdmin
from poradnia.ai_assistant.models import N8nSimilarCasesRequest, SimilarCasesIndexState
from poradnia.ai_assistant.tasks import (
    delete_case_from_similar_index_task,
    sync_case_similar_index_task,
    sync_similar_cases_index_task,
)
from poradnia.cases.factories import CaseFactory
from poradnia.cases.models import Case, DeleteCaseProxy, _normalize_whitespace
from poradnia.letters.factories import AttachmentFactory, LetterFactory
from poradnia.letters.models import Letter
from poradnia.users.factories import StaffFactory, UserFactory

CLIENT_TEXT = (
    "Złożyłem wniosek o informację publiczną do gminy, a gmina przedłużyła "
    "termin bez podania przyczyny. Co mogę zrobić? "
) * 3

INDEX_SETTINGS = {
    "N8N_SIMILAR_CASES_INDEX_WEBHOOK": "https://n8n.example.test/webhook/index",
    "N8N_SIMILAR_CASES_INDEX_WEBHOOK_TOKEN": "index-secret",
    "APP_MODE": "TEST",
}

SYNC_TASK = "poradnia.ai_assistant.tasks.sync_case_similar_index_task.apply_async"
DELETE_TASK = (
    "poradnia.ai_assistant.tasks.delete_case_from_similar_index_task.apply_async"
)
BULK_TASK = "poradnia.ai_assistant.tasks.sync_similar_cases_index_task.delay"
HTTP_POST = "poradnia.ai_assistant.similar_cases.requests.post"


def dip_scope(**kwargs):
    defaults = {"is_dip": True, "is_local_government": False, "is_slapp": False}
    defaults.update(kwargs)
    return ScopeFactory(**defaults)


def make_case(
    status=Case.STATUS.closed,
    advice=True,
    visible=True,
    institution_kind="normal",
    scope="in",
    text=CLIENT_TEXT,
    client=None,
    name=None,
):
    """A case with one client letter; by default eligible for the index."""
    client = client or UserFactory(is_staff=False)
    case_kwargs = {"client": client}
    if name:
        case_kwargs["name"] = name
    case = CaseFactory(**case_kwargs)
    if text:
        LetterFactory(
            case=case, created_by=client, created_by_is_staff=False, text=text
        )
    if advice:
        advice_kwargs = {"case": case, "visible": visible}
        if institution_kind == "normal":
            advice_kwargs["institution_kind"] = InstitutionKindFactory()
        elif institution_kind == "undefined":
            advice_kwargs["institution_kind"] = InstitutionKindFactory(
                is_undefined=True
            )
        elif institution_kind is not None:
            advice_kwargs["institution_kind"] = institution_kind
        if scope == "in":
            advice_kwargs["scope"] = dip_scope()
        elif scope == "out":
            advice_kwargs["scope"] = ScopeFactory(is_out_of_scope=True)
        elif scope is not None:
            advice_kwargs["scope"] = scope
        AdviceFactory(**advice_kwargs)
    Case.objects.filter(pk=case.pk).update(status=status, status_changed=timezone.now())
    return Case.objects.get(pk=case.pk)


def index_response(**data):
    response = MagicMock()
    response.json.return_value = {"ok": True, **data}
    return response


class EligibleForSimilarCasesTestCase(TestCase):
    def test_only_the_all_good_combination_is_eligible(self):
        variants = {
            "eligible": {},
            "open": {"status": Case.STATUS.assigned},
            "no_advice": {"advice": False},
            "not_visible": {"visible": False},
            "no_kind": {"institution_kind": None},
            "undefined_kind": {"institution_kind": "undefined"},
            "no_scope": {"scope": None},
            "out_of_scope": {"scope": "out"},
        }
        cases = {label: make_case(**kwargs) for label, kwargs in variants.items()}

        eligible = set(
            Case.objects.eligible_for_similar_cases().values_list("pk", flat=True)
        )

        self.assertEqual(eligible, {cases["eligible"].pk})

    def test_combinations_of_problems_are_not_eligible(self):
        make_case(status=Case.STATUS.free, visible=False, scope="out")
        make_case(advice=True, institution_kind="undefined", scope=None)
        self.assertFalse(Case.objects.eligible_for_similar_cases().exists())

    @override_settings(**INDEX_SETTINGS)
    @patch(HTTP_POST)
    def test_merged_source_case_without_client_text_is_skipped(self, mock_post):
        case = make_case(text="")
        self.assertIn(case, Case.objects.eligible_for_similar_cases())

        result = sync_case_similar_index_task(case.pk)

        self.assertEqual(result["action"], "skip")
        mock_post.assert_not_called()


class GetSimilarCasesTextTestCase(TestCase):
    def setUp(self):
        self.client_user = UserFactory(is_staff=False)
        self.case = CaseFactory(client=self.client_user)

    def _letter(self, text, staff=False):
        author = StaffFactory() if staff else self.client_user
        return LetterFactory(
            case=self.case, created_by=author, created_by_is_staff=staff, text=text
        )

    def test_letters_first_then_attachments_and_staff_letters_excluded(self):
        first = self._letter("first letter")
        AttachmentFactory(letter=first, text_content="first attachment")
        self._letter("staff reply", staff=True)
        second = self._letter("second letter")
        AttachmentFactory(letter=second, text_content="second attachment")

        text = self.case.get_similar_cases_text(max_chars=1000)

        self.assertEqual(
            text,
            "first letter\n\nsecond letter\n\nfirst attachment\n\nsecond attachment",
        )
        self.assertNotIn("staff reply", text)

    def test_first_letter_is_kept_whole_and_later_text_fills_the_budget(self):
        self._letter("a" * 50)
        self._letter("b" * 50)
        AttachmentFactory(letter=self._letter("c" * 10), text_content="d" * 50)

        text = self.case.get_similar_cases_text(max_chars=80)

        self.assertEqual(len(text), 80)
        self.assertTrue(text.startswith("a" * 50 + "\n\n"))
        self.assertNotIn("d", text)

    def test_first_letter_longer_than_budget_is_cut(self):
        self._letter("x" * 200)
        self.assertEqual(self.case.get_similar_cases_text(max_chars=120), "x" * 120)

    def test_whitespace_is_normalised(self):
        self._letter("one\t\t two   three  \r\n\n\n\n\n\nfour")
        self.assertEqual(
            self.case.get_similar_cases_text(max_chars=1000),
            "one two three\n\n\nfour",
        )

    def test_normalize_whitespace_of_empty_text(self):
        self.assertEqual(_normalize_whitespace(None), "")
        self.assertEqual(_normalize_whitespace(""), "")

    @override_settings(SIMILAR_CASES_TEXT_MAX_CHARS=30)
    def test_max_chars_defaults_to_setting(self):
        self._letter("y" * 100)
        self.assertEqual(len(self.case.get_similar_cases_text()), 30)

    def test_get_client_messages_content_is_unchanged(self):
        first = self._letter("first letter")
        AttachmentFactory(letter=first, text_content="first attachment")
        self._letter("second letter")
        self.assertEqual(
            self.case.get_client_messages_content(),
            "first letter\n\nfirst attachment\n\nsecond letter",
        )


@override_settings(**INDEX_SETTINGS)
class SyncCaseSimilarIndexTaskTestCase(TestCase):
    def setUp(self):
        self.case = make_case()

    @patch(HTTP_POST)
    def test_not_eligible_without_state_is_skipped(self, mock_post):
        case = make_case(status=Case.STATUS.assigned)
        result = sync_case_similar_index_task(case.pk)
        self.assertEqual(result, {"case_pk": case.pk, "action": "skip"})
        mock_post.assert_not_called()

    @patch(HTTP_POST)
    def test_missing_case_without_state_is_skipped(self, mock_post):
        result = sync_case_similar_index_task(999999)
        self.assertEqual(result["action"], "skip")
        mock_post.assert_not_called()

    @patch(HTTP_POST, return_value=index_response(points=2))
    def test_first_sync_upserts_with_text(self, mock_post):
        result = sync_case_similar_index_task(self.case.pk)

        self.assertEqual(result, {"case_pk": self.case.pk, "action": "upsert"})
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], INDEX_SETTINGS["N8N_SIMILAR_CASES_INDEX_WEBHOOK"])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer index-secret")
        self.assertEqual(kwargs["timeout"], 180)
        body = kwargs["json"]
        text = self.case.get_similar_cases_text()
        advice = self.case.advice
        self.assertEqual(
            body,
            {
                "action": "upsert",
                "environment": "TEST",
                "reembed": True,
                "case": {
                    "id": self.case.pk,
                    "institution_kind_id": advice.institution_kind_id,
                    "institution_kind_name": advice.institution_kind.name,
                    "scope_id": advice.scope_id,
                    "scope_flags": {
                        "is_dip": True,
                        "is_local_government": False,
                        "is_slapp": False,
                    },
                    "closed_at": self.case.status_changed.date().isoformat(),
                    "content_hash": similar_cases.content_hash(text),
                },
                "text": text,
            },
        )
        state = SimilarCasesIndexState.objects.get(case=self.case)
        self.assertEqual(state.status, "indexed")
        self.assertEqual(state.points, 2)
        self.assertEqual(state.content_hash, similar_cases.content_hash(text))
        self.assertEqual(state.metadata_hash, similar_cases.metadata_hash(self.case))
        self.assertIsNotNone(state.synced_at)

    @patch(HTTP_POST, return_value=index_response(points=2))
    def test_second_sync_with_equal_hashes_is_noop(self, mock_post):
        sync_case_similar_index_task(self.case.pk)
        mock_post.reset_mock()

        result = sync_case_similar_index_task(self.case.pk)

        self.assertEqual(result["action"], "noop")
        mock_post.assert_not_called()

    @patch(HTTP_POST, return_value=index_response(points=2))
    def test_metadata_change_sends_metadata_only(self, mock_post):
        sync_case_similar_index_task(self.case.pk)
        advice = self.case.advice
        advice.institution_kind = InstitutionKindFactory()
        advice.save()
        mock_post.reset_mock()

        result = sync_case_similar_index_task(self.case.pk)

        self.assertEqual(result["action"], "metadata")
        body = mock_post.call_args.kwargs["json"]
        self.assertFalse(body["reembed"])
        self.assertIsNone(body["text"])
        self.assertEqual(
            body["case"]["institution_kind_id"], advice.institution_kind_id
        )
        state = SimilarCasesIndexState.objects.get(case=self.case)
        self.assertEqual(
            state.metadata_hash,
            similar_cases.metadata_hash(Case.objects.get(pk=self.case.pk)),
        )

    @patch(HTTP_POST, return_value=index_response(points=2))
    def test_scope_flag_change_changes_metadata_hash(self, mock_post):
        sync_case_similar_index_task(self.case.pk)
        scope = self.case.advice.scope
        scope.is_local_government = True
        scope.save()
        mock_post.reset_mock()

        result = sync_case_similar_index_task(self.case.pk)

        self.assertEqual(result["action"], "metadata")
        body = mock_post.call_args.kwargs["json"]
        self.assertTrue(body["case"]["scope_flags"]["is_local_government"])

    @patch(HTTP_POST)
    def test_lost_points_on_metadata_update_trigger_reembed(self, mock_post):
        mock_post.return_value = index_response(points=2)
        sync_case_similar_index_task(self.case.pk)
        advice = self.case.advice
        advice.institution_kind = InstitutionKindFactory()
        advice.save()
        mock_post.reset_mock()
        mock_post.side_effect = [index_response(points=0), index_response(points=1)]

        result = sync_case_similar_index_task(self.case.pk)

        self.assertEqual(result["action"], "upsert")
        first, second = (c.kwargs["json"] for c in mock_post.call_args_list)
        self.assertFalse(first["reembed"])
        self.assertTrue(second["reembed"])
        self.assertEqual(second["text"], self.case.get_similar_cases_text())
        self.assertEqual(SimilarCasesIndexState.objects.get(case=self.case).points, 1)

    @patch(HTTP_POST, return_value=index_response(points=2))
    def test_content_change_reembeds(self, mock_post):
        sync_case_similar_index_task(self.case.pk)
        LetterFactory(
            case=self.case,
            created_by=self.case.client,
            created_by_is_staff=False,
            text="nowa wiadomość",
        )
        mock_post.reset_mock()

        result = sync_case_similar_index_task(self.case.pk)

        self.assertEqual(result["action"], "upsert")
        body = mock_post.call_args.kwargs["json"]
        self.assertTrue(body["reembed"])
        self.assertIn("nowa wiadomość", body["text"])

    @patch(HTTP_POST, return_value=index_response(points=0))
    def test_zero_points_store_empty_and_then_noop(self, mock_post):
        sync_case_similar_index_task(self.case.pk)
        state = SimilarCasesIndexState.objects.get(case=self.case)
        self.assertEqual(state.status, "empty")
        self.assertEqual(state.points, 0)
        mock_post.reset_mock()

        result = sync_case_similar_index_task(self.case.pk)

        self.assertEqual(result["action"], "noop")
        mock_post.assert_not_called()

    @patch(HTTP_POST, return_value=index_response(points=2))
    def test_reopened_case_with_state_is_deleted(self, mock_post):
        sync_case_similar_index_task(self.case.pk)
        Case.objects.filter(pk=self.case.pk).update(status=Case.STATUS.assigned)
        mock_post.reset_mock()
        mock_post.return_value = index_response()

        result = sync_case_similar_index_task(self.case.pk)

        self.assertEqual(result, {"case_pk": self.case.pk, "action": "delete"})
        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {"action": "delete", "environment": "TEST", "case_id": self.case.pk},
        )
        self.assertFalse(SimilarCasesIndexState.objects.filter(case=self.case).exists())

    @override_settings(SIMILAR_CASES_MIN_TEXT_CHARS=10000)
    @patch(HTTP_POST, return_value=index_response())
    def test_too_short_text_with_state_is_deleted(self, mock_post):
        SimilarCasesIndexState.objects.create(
            case=self.case, status="indexed", points=1
        )
        result = sync_case_similar_index_task(self.case.pk)
        self.assertEqual(result["action"], "delete")

    @patch(HTTP_POST)
    def test_delete_error_records_error_and_keeps_state(self, mock_post):
        SimilarCasesIndexState.objects.create(
            case=self.case, status="indexed", points=1
        )
        Case.objects.filter(pk=self.case.pk).update(status=Case.STATUS.assigned)
        mock_post.side_effect = requests_lib.ConnectionError("n8n down")

        with self.assertRaises(requests_lib.ConnectionError):
            sync_case_similar_index_task(self.case.pk)

        state = SimilarCasesIndexState.objects.get(case=self.case)
        self.assertEqual((state.status, state.attempts), ("error", 1))
        self.assertIn("n8n down", state.error)

    @override_settings(N8N_SIMILAR_CASES_INDEX_WEBHOOK="")
    @patch(HTTP_POST)
    def test_missing_index_webhook_raises_improperly_configured(self, mock_post):
        with self.assertRaises(ImproperlyConfigured):
            similar_cases.index_delete(self.case.pk)
        mock_post.assert_not_called()

    @patch(HTTP_POST)
    def test_http_error_records_error_and_raises(self, mock_post):
        mock_post.side_effect = requests_lib.ConnectionError("n8n down")

        with self.assertRaises(requests_lib.ConnectionError):
            sync_case_similar_index_task(self.case.pk)
        with self.assertRaises(requests_lib.ConnectionError):
            sync_case_similar_index_task(self.case.pk)

        state = SimilarCasesIndexState.objects.get(case=self.case)
        self.assertEqual(state.status, "error")
        self.assertEqual(state.attempts, 2)
        self.assertIn("n8n down", state.error)
        self.assertIsNone(state.synced_at)

    @patch(HTTP_POST)
    def test_error_state_reembeds_and_resets_attempts(self, mock_post):
        SimilarCasesIndexState.objects.create(
            case=self.case,
            status="error",
            attempts=3,
            error="boom",
            content_hash=similar_cases.content_hash(self.case.get_similar_cases_text()),
            metadata_hash=similar_cases.metadata_hash(self.case),
        )
        mock_post.return_value = index_response(points=1)

        result = sync_case_similar_index_task(self.case.pk)

        self.assertEqual(result["action"], "upsert")
        self.assertTrue(mock_post.call_args.kwargs["json"]["reembed"])
        state = SimilarCasesIndexState.objects.get(case=self.case)
        self.assertEqual(
            (state.status, state.attempts, state.error), ("indexed", 0, "")
        )

    @patch(HTTP_POST)
    def test_ok_false_is_an_error(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"ok": False, "error": "qdrant down"}
        mock_post.return_value = response

        with self.assertRaises(similar_cases.IndexWebhookError):
            sync_case_similar_index_task(self.case.pk)

        state = SimilarCasesIndexState.objects.get(case=self.case)
        self.assertEqual(state.status, "error")
        self.assertIn("qdrant down", state.error)

    @patch(HTTP_POST)
    def test_non_2xx_is_an_error(self, mock_post):
        response = MagicMock()
        response.raise_for_status.side_effect = requests_lib.HTTPError("500")
        mock_post.return_value = response

        with self.assertRaises(requests_lib.HTTPError):
            sync_case_similar_index_task(self.case.pk)

    @patch(HTTP_POST, return_value=index_response())
    def test_delete_task_posts_delete_without_reading_the_case(self, mock_post):
        result = delete_case_from_similar_index_task(424242)
        self.assertEqual(result, {"case_pk": 424242, "action": "delete"})
        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {"action": "delete", "environment": "TEST", "case_id": 424242},
        )

    def test_reconcile_refuses_an_empty_list(self):
        with self.assertRaises(ValueError):
            similar_cases.index_reconcile([])


@override_settings(SIMILAR_CASES_INDEX_ENABLED=True)
class SimilarCasesSignalsTestCase(TestCase):
    def setUp(self):
        self.actor = StaffFactory()

    @patch(SYNC_TASK)
    def test_close_enqueues_sync(self, mock_sync):
        case = make_case(status=Case.STATUS.assigned)
        with self.captureOnCommitCallbacks(execute=True):
            case.close(actor=self.actor, notify=False)
            case.save()
        mock_sync.assert_called_once_with(args=[case.pk], countdown=60)

    @patch(SYNC_TASK)
    def test_reopen_enqueues_sync(self, mock_sync):
        case = make_case()
        with self.captureOnCommitCallbacks(execute=True):
            case.update_status(reopen=True)
        self.assertNotEqual(case.status, Case.STATUS.closed)
        mock_sync.assert_called_once_with(args=[case.pk], countdown=60)

    @patch(SYNC_TASK)
    def test_status_change_saved_with_update_fields_enqueues_sync(self, mock_sync):
        case = make_case(status=Case.STATUS.assigned)
        with self.captureOnCommitCallbacks(execute=True):
            case.status = Case.STATUS.closed
            case.save(update_fields=["status", "status_changed"])
        mock_sync.assert_called_once_with(args=[case.pk], countdown=60)

    @patch(SYNC_TASK)
    def test_non_status_save_does_not_enqueue(self, mock_sync):
        case = make_case()
        with self.captureOnCommitCallbacks(execute=True):
            case.name = "nowa nazwa"
            case.save()
            case.handled = True
            case.save()
        mock_sync.assert_not_called()

    @patch(SYNC_TASK)
    def test_case_creation_does_not_enqueue(self, mock_sync):
        with self.captureOnCommitCallbacks(execute=True):
            CaseFactory()
        mock_sync.assert_not_called()

    @patch(SYNC_TASK)
    def test_advice_edit_on_closed_case_enqueues(self, mock_sync):
        case = make_case()
        with self.captureOnCommitCallbacks(execute=True):
            case.advice.visible = False
            case.advice.save()
        mock_sync.assert_called_once_with(args=[case.pk], countdown=60)

    @patch(SYNC_TASK)
    def test_advice_scope_change_on_closed_case_enqueues(self, mock_sync):
        case = make_case()
        with self.captureOnCommitCallbacks(execute=True):
            case.advice.scope = dip_scope(is_slapp=True)
            case.advice.save()
        mock_sync.assert_called_once_with(args=[case.pk], countdown=60)

    @patch(SYNC_TASK)
    def test_advice_edit_on_open_case_without_state_does_not_enqueue(self, mock_sync):
        case = make_case(status=Case.STATUS.assigned)
        with self.captureOnCommitCallbacks(execute=True):
            case.advice.visible = False
            case.advice.save()
        mock_sync.assert_not_called()

    @patch(SYNC_TASK)
    def test_advice_edit_on_open_case_with_state_enqueues(self, mock_sync):
        case = make_case(status=Case.STATUS.assigned)
        SimilarCasesIndexState.objects.create(case=case, status="indexed", points=1)
        with self.captureOnCommitCallbacks(execute=True):
            case.advice.save()
        mock_sync.assert_called_once_with(args=[case.pk], countdown=60)

    @patch(SYNC_TASK)
    def test_advice_delete_on_closed_case_enqueues(self, mock_sync):
        case = make_case()
        with self.captureOnCommitCallbacks(execute=True):
            case.advice.delete()
        mock_sync.assert_called_once_with(args=[case.pk], countdown=60)

    @patch(BULK_TASK)
    def test_scope_flag_edit_enqueues_bulk_sync(self, mock_bulk):
        scope = dip_scope()
        with self.captureOnCommitCallbacks(execute=True):
            scope.is_slapp = True
            scope.save()
        mock_bulk.assert_called_once_with(
            mode="incremental", scope_ids=[scope.pk], force_check=True
        )

    @patch(BULK_TASK)
    def test_scope_out_of_scope_flag_edit_enqueues_bulk_sync(self, mock_bulk):
        scope = dip_scope()
        with self.captureOnCommitCallbacks(execute=True):
            scope.is_out_of_scope = True
            scope.save()
        mock_bulk.assert_called_once()

    @patch(BULK_TASK)
    def test_scope_name_edit_and_creation_do_not_enqueue(self, mock_bulk):
        with self.captureOnCommitCallbacks(execute=True):
            scope = dip_scope()
            scope.name = "inna nazwa"
            scope.save()
        mock_bulk.assert_not_called()

    @patch(SYNC_TASK)
    @patch(DELETE_TASK)
    def test_case_delete_enqueues_delete(self, mock_delete, mock_sync):
        case = make_case()
        pk = case.pk
        with self.captureOnCommitCallbacks(execute=True):
            case.delete()
        mock_delete.assert_called_once_with(args=[pk])

    @patch(SYNC_TASK)
    @patch(DELETE_TASK)
    def test_queryset_delete_through_cleanup_proxy_enqueues_deletes(
        self, mock_delete, mock_sync
    ):
        first, second = make_case(), make_case()
        with self.captureOnCommitCallbacks(execute=True):
            DeleteCaseProxy.objects.filter(pk__in=[first.pk, second.pk]).delete()
        self.assertCountEqual(
            mock_delete.call_args_list,
            [call(args=[first.pk]), call(args=[second.pk])],
        )

    @override_settings(SIMILAR_CASES_INDEX_ENABLED=False)
    @patch(BULK_TASK)
    @patch(SYNC_TASK)
    @patch(DELETE_TASK)
    def test_switch_off_enqueues_nothing(self, mock_delete, mock_sync, mock_bulk):
        case = make_case(status=Case.STATUS.assigned)
        scope = case.advice.scope
        with self.captureOnCommitCallbacks(execute=True):
            case.close(actor=self.actor, notify=False)
            case.save()
            case.advice.save()
            scope.is_slapp = True
            scope.save()
            case.delete()
        mock_sync.assert_not_called()
        mock_delete.assert_not_called()
        mock_bulk.assert_not_called()


@override_settings(SIMILAR_CASES_INDEX_ENABLED=True, **INDEX_SETTINGS)
@patch(SYNC_TASK)
class SyncSimilarCasesIndexTaskTestCase(TestCase):
    def _enqueued(self, mock_sync):
        return [c.kwargs["args"][0] for c in mock_sync.call_args_list]

    def _state(self, case, **kwargs):
        defaults = {"status": "indexed", "points": 1, "synced_at": timezone.now()}
        defaults.update(kwargs)
        return SimilarCasesIndexState.objects.create(case=case, **defaults)

    def _make_fresh(self, case):
        """Mark a case and its advice as modified well before its last sync."""
        past = timezone.now() - timedelta(days=10)
        Case.objects.filter(pk=case.pk).update(modified_on=past)
        case.advice.__class__.objects.filter(pk=case.advice.pk).update(modified_on=past)

    def test_unknown_mode_raises(self, mock_sync):
        with self.assertRaises(ValueError):
            sync_similar_cases_index_task(mode="everything")

    @override_settings(SIMILAR_CASES_INDEX_ENABLED=False)
    def test_switch_off_is_a_noop(self, mock_sync):
        make_case()
        result = sync_similar_cases_index_task(mode="initial")
        self.assertEqual(result, {"mode": "initial", "skipped": "disabled"})
        mock_sync.assert_not_called()

    @override_settings(SIMILAR_CASES_INDEX_ENABLED=False)
    def test_switch_off_with_explicit_case_ids_runs(self, mock_sync):
        case, other = make_case(), make_case()
        sync_similar_cases_index_task(mode="initial", case_ids=[case.pk])
        self.assertEqual(self._enqueued(mock_sync), [case.pk])
        self.assertNotIn(other.pk, self._enqueued(mock_sync))

    def test_initial_enqueues_eligible_without_state_staggered(self, mock_sync):
        first, second, indexed = make_case(), make_case(), make_case()
        make_case(status=Case.STATUS.assigned)
        self._state(indexed)

        result = sync_similar_cases_index_task(mode="initial", pause_seconds=5)

        self.assertEqual(
            mock_sync.call_args_list,
            [call(args=[second.pk], countdown=0), call(args=[first.pk], countdown=5)],
        )
        self.assertEqual(result["enqueued"], 2)

    def test_initial_limit(self, mock_sync):
        _, last = make_case(), make_case()
        sync_similar_cases_index_task(mode="initial", limit=1)
        self.assertEqual(self._enqueued(mock_sync), [last.pk])

    def test_initial_force_reembed_resets_state(self, mock_sync):
        fresh, indexed = make_case(), make_case()
        self._state(indexed, content_hash="x")

        sync_similar_cases_index_task(mode="initial", force_reembed=True)

        self.assertEqual(self._enqueued(mock_sync), [indexed.pk, fresh.pk])
        self.assertFalse(SimilarCasesIndexState.objects.exists())

    @override_settings(SIMILAR_CASES_SYNC_PAUSE_SECONDS=7)
    def test_pause_defaults_to_setting(self, mock_sync):
        make_case(), make_case()
        sync_similar_cases_index_task(mode="initial")
        self.assertEqual(mock_sync.call_args_list[1].kwargs["countdown"], 7)

    def test_incremental_picks_stale_error_and_no_longer_eligible(self, mock_sync):
        no_state = make_case()
        fresh = make_case()
        self._make_fresh(fresh)
        self._state(fresh)
        case_modified = make_case()
        self._make_fresh(case_modified)
        self._state(case_modified)
        Case.objects.filter(pk=case_modified.pk).update(
            modified_on=timezone.now() + timedelta(days=1)
        )
        advice_modified = make_case()
        self._make_fresh(advice_modified)
        self._state(advice_modified)
        advice_modified.advice.__class__.objects.filter(
            pk=advice_modified.advice.pk
        ).update(modified_on=timezone.now() + timedelta(days=1))
        errored = make_case()
        self._make_fresh(errored)
        self._state(errored, status="error")
        reopened = make_case(status=Case.STATUS.assigned)
        self._state(reopened)

        result = sync_similar_cases_index_task(mode="incremental")

        self.assertCountEqual(
            self._enqueued(mock_sync),
            [
                no_state.pk,
                case_modified.pk,
                advice_modified.pk,
                errored.pk,
                reopened.pk,
            ],
        )
        self.assertNotIn(fresh.pk, self._enqueued(mock_sync))
        self.assertEqual((result["to_sync"], result["to_delete"]), (4, 1))

    def test_scope_force_check_enqueues_regardless_of_synced_at(self, mock_sync):
        scope = dip_scope()
        fresh = make_case(scope=scope)
        self._make_fresh(fresh)
        self._state(fresh)
        now_out_of_scope_case = make_case(scope=scope)
        self._state(now_out_of_scope_case)
        open_unindexed = make_case(scope=scope, status=Case.STATUS.assigned)
        other_scope = make_case()

        sync_similar_cases_index_task(
            mode="incremental", scope_ids=[scope.pk], force_check=True
        )

        enqueued = self._enqueued(mock_sync)
        self.assertCountEqual(enqueued, [fresh.pk, now_out_of_scope_case.pk])
        self.assertNotIn(open_unindexed.pk, enqueued)
        self.assertNotIn(other_scope.pk, enqueued)

    def test_dry_run_enqueues_nothing(self, mock_sync):
        make_case(), make_case()
        result = sync_similar_cases_index_task(mode="initial", dry_run=True)
        self.assertEqual(result["to_sync"], 2)
        self.assertEqual(result["enqueued"], 0)
        mock_sync.assert_not_called()

    @patch(HTTP_POST)
    def test_reconcile_resets_and_reenqueues_missing(self, mock_post, mock_sync):
        indexed, missing = make_case(), make_case()
        self._state(indexed, points=2)
        self._state(missing, points=1)
        empty = make_case()
        self._state(empty, status="empty", points=0)
        mock_post.return_value = index_response(
            orphans_deleted=[777, 778], missing=[missing.pk]
        )

        result = sync_similar_cases_index_task(mode="reconcile")

        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {
                "action": "reconcile",
                "environment": "TEST",
                "case_ids": [indexed.pk, missing.pk],
            },
        )
        self.assertEqual((result["orphans_deleted"], result["missing"]), (2, 1))
        self.assertFalse(SimilarCasesIndexState.objects.filter(case=missing).exists())
        self.assertTrue(SimilarCasesIndexState.objects.filter(case=indexed).exists())
        self.assertEqual(self._enqueued(mock_sync), [missing.pk])

    @patch(HTTP_POST)
    def test_reconcile_without_indexed_cases_never_calls_n8n(
        self, mock_post, mock_sync
    ):
        make_case()
        result = sync_similar_cases_index_task(mode="reconcile")
        self.assertEqual(result["skipped"], "no_indexed_cases")
        mock_post.assert_not_called()

    @patch(HTTP_POST)
    def test_reconcile_dry_run_never_calls_n8n(self, mock_post, mock_sync):
        self._state(make_case(), points=1)
        result = sync_similar_cases_index_task(mode="reconcile", dry_run=True)
        self.assertEqual(result["case_ids"], 1)
        mock_post.assert_not_called()

    def test_reconcile_refuses_narrowing(self, mock_sync):
        case = make_case()
        for kwargs in ({"case_ids": [case.pk]}, {"limit": 1}, {"scope_ids": [1]}):
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                sync_similar_cases_index_task(mode="reconcile", **kwargs)


@override_settings(SIMILAR_CASES_INDEX_ENABLED=False, **INDEX_SETTINGS)
class SyncSimilarCasesIndexCommandTestCase(TestCase):
    @patch(SYNC_TASK)
    def test_sync_dry_run_with_case_ids_prints_counts(self, mock_sync):
        case = make_case()
        make_case()  # eligible too, but not in --case-ids
        out = StringIO()

        call_command(
            "sync_similar_cases_index",
            "--mode",
            "initial",
            "--case-ids",
            f"{case.pk}",
            "--dry-run",
            "--sync",
            stdout=out,
        )

        self.assertIn("to_sync=1", out.getvalue())
        self.assertIn("dry_run=True", out.getvalue())
        mock_sync.assert_not_called()

    @patch(SYNC_TASK)
    def test_sync_with_case_ids_enqueues_with_switch_off(self, mock_sync):
        first, second = make_case(), make_case()
        call_command(
            "sync_similar_cases_index",
            "--mode",
            "initial",
            "--case-ids",
            f"{first.pk},{second.pk}",
            "--pause-seconds",
            "2",
            "--no-dry-run",
            "--sync",
            stdout=StringIO(),
        )
        self.assertEqual(
            mock_sync.call_args_list,
            [call(args=[second.pk], countdown=0), call(args=[first.pk], countdown=2)],
        )

    @patch("poradnia.ai_assistant.tasks.sync_similar_cases_index_task.delay")
    def test_default_enqueues_a_dry_run(self, mock_delay):
        mock_delay.return_value.id = "task-123"
        out = StringIO()
        call_command("sync_similar_cases_index", "--limit", "5", stdout=out)
        mock_delay.assert_called_once_with(
            mode="incremental",
            pause_seconds=None,
            limit=5,
            case_ids=None,
            scope_ids=None,
            force_check=False,
            force_reembed=False,
            dry_run=True,
        )
        self.assertTrue(out.getvalue().startswith("DRY RUN"))
        self.assertIn("task-123", out.getvalue())

    @patch("poradnia.ai_assistant.tasks.sync_similar_cases_index_task.delay")
    def test_no_dry_run_skips_the_notice(self, mock_delay):
        mock_delay.return_value.id = "task-123"
        out = StringIO()
        call_command("sync_similar_cases_index", "--all", "--no-dry-run", stdout=out)
        self.assertIs(mock_delay.call_args.kwargs["dry_run"], False)
        self.assertIsNone(mock_delay.call_args.kwargs["limit"])
        self.assertNotIn("DRY RUN", out.getvalue())

    def test_selection_argument_is_required(self):
        with self.assertRaises(CommandError):
            call_command("sync_similar_cases_index", stdout=StringIO())

    def test_selection_arguments_are_exclusive(self):
        for args in (
            ("--all", "--limit", "5"),
            ("--all", "--case-ids", "1"),
            ("--limit", "5", "--case-ids", "1"),
        ):
            with self.subTest(args=args), self.assertRaises(CommandError):
                call_command("sync_similar_cases_index", *args, stdout=StringIO())

    @patch("poradnia.ai_assistant.tasks.sync_similar_cases_index_task.delay")
    def test_scope_ids_and_force_check_are_passed_on(self, mock_delay):
        mock_delay.return_value.id = "task-123"
        call_command(
            "sync_similar_cases_index",
            "--all",
            "--scope-ids",
            "3,4",
            "--force-check",
            stdout=StringIO(),
        )
        self.assertEqual(mock_delay.call_args.kwargs["scope_ids"], [3, 4])
        self.assertIs(mock_delay.call_args.kwargs["force_check"], True)

    @patch("poradnia.ai_assistant.tasks.sync_similar_cases_index_task.delay")
    def test_reconcile_with_all_enqueues(self, mock_delay):
        mock_delay.return_value.id = "task-123"
        call_command(
            "sync_similar_cases_index",
            "--mode",
            "reconcile",
            "--all",
            stdout=StringIO(),
        )
        self.assertEqual(mock_delay.call_args.kwargs["mode"], "reconcile")

    def test_reconcile_with_limit_is_refused(self):
        with self.assertRaises(CommandError):
            call_command(
                "sync_similar_cases_index",
                "--mode",
                "reconcile",
                "--limit",
                "5",
                stdout=StringIO(),
            )

    def test_reconcile_with_scope_ids_is_refused(self):
        with self.assertRaises(CommandError):
            call_command(
                "sync_similar_cases_index",
                "--mode",
                "reconcile",
                "--all",
                "--scope-ids",
                "1",
                stdout=StringIO(),
            )

    def test_reconcile_with_case_ids_is_refused(self):
        with self.assertRaises(CommandError):
            call_command(
                "sync_similar_cases_index",
                "--mode",
                "reconcile",
                "--case-ids",
                "1",
                stdout=StringIO(),
            )

    def test_invalid_case_ids(self):
        with self.assertRaises(CommandError):
            call_command(
                "sync_similar_cases_index", "--case-ids", "1,x", stdout=StringIO()
            )


class SimilarCasesPeriodicTasksMigrationTestCase(TestCase):
    def test_beat_tasks_exist_and_are_disabled(self):
        from django_celery_beat.models import PeriodicTask

        tasks = {
            task.name: task
            for task in PeriodicTask.objects.filter(
                task="poradnia.ai_assistant.tasks.sync_similar_cases_index_task"
            )
        }
        self.assertEqual(
            set(tasks),
            {
                "sync-similar-cases-index-incremental",
                "sync-similar-cases-index-reconcile",
            },
        )
        incremental = tasks["sync-similar-cases-index-incremental"]
        reconcile = tasks["sync-similar-cases-index-reconcile"]
        self.assertFalse(incremental.enabled or reconcile.enabled)
        self.assertEqual(json.loads(incremental.kwargs), {"mode": "incremental"})
        self.assertEqual(json.loads(reconcile.kwargs), {"mode": "reconcile"})
        self.assertEqual(
            (incremental.crontab.hour, incremental.crontab.minute), ("2", "17")
        )
        self.assertEqual(
            (
                reconcile.crontab.day_of_week,
                reconcile.crontab.hour,
                reconcile.crontab.minute,
            ),
            ("0", "3", "23"),
        )
        self.assertEqual(str(incremental.crontab.timezone), "Europe/Warsaw")


CALLBACK_TOKEN = "similar-callback-secret"


@override_settings(N8N_SIMILAR_CASES_CALLBACK_TOKEN=CALLBACK_TOKEN)
class N8nSimilarCasesCallbackViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = views_module.N8nSimilarCasesCallbackView.as_view()
        self.kind = InstitutionKindFactory(name="Gmina")
        self.scope = dip_scope(name="DIP")
        self.requesting = make_case(
            status=Case.STATUS.assigned,
            institution_kind=self.kind,
            scope=self.scope,
        )
        self.similar_request = N8nSimilarCasesRequest.objects.create(
            request_id="sim-1",
            environment="TEST",
            question="q",
            case=self.requesting,
            institution_kind=self.kind,
            institution_kind_source="advice",
            scope=self.scope,
            scope_source="advice",
        )

    def _match(self, **kwargs):
        """A closed case that matches the request's filters."""
        kwargs.setdefault("institution_kind", self.kind)
        kwargs.setdefault("scope", dip_scope())
        return make_case(**kwargs)

    def _post(self, payload, token=CALLBACK_TOKEN):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
        request = self.factory.post(
            "/", data=body, content_type="application/json", **headers
        )
        return self.view(request)

    def _entry(self, case, score=0.7, reason="Ta sama sytuacja."):
        return {"case_id": case.pk, "score": score, "reason": reason}

    def _payload(self, entries, **extra):
        return {"request_id": "sim-1", "similar_cases": entries, **extra}

    def _refresh(self):
        self.similar_request.refresh_from_db()
        return self.similar_request

    def test_url_is_mounted(self):
        self.assertEqual(
            reverse("ai_assistant:similar-cases-callback"),
            "/ai-assistant/api/similar-cases",
        )

    @override_settings(N8N_SIMILAR_CASES_CALLBACK_TOKEN="")
    def test_token_not_configured_returns_503(self):
        self.assertEqual(self._post(self._payload([])).status_code, 503)

    def test_missing_token_returns_401(self):
        self.assertEqual(self._post(self._payload([]), token=None).status_code, 401)

    def test_invalid_token_returns_401(self):
        self.assertEqual(self._post(self._payload([]), token="wrong").status_code, 401)

    def test_articles_token_is_not_accepted(self):
        with override_settings(N8N_ARTICLES_SEARCH_CALLBACK_TOKEN="articles"):
            self.assertEqual(
                self._post(self._payload([]), token="articles").status_code, 401
            )

    def test_invalid_json_returns_400(self):
        self.assertEqual(self._post(b"{bad").status_code, 400)

    def test_missing_request_id_returns_400(self):
        self.assertEqual(self._post({"similar_cases": []}).status_code, 400)

    def test_unknown_request_id_returns_404(self):
        response = self._post({"request_id": "nope", "similar_cases": []})
        self.assertEqual(response.status_code, 404)

    def test_error_marks_failed_without_letter(self):
        response = self._post({"request_id": "sim-1", "error": "judge exploded"})
        self.assertEqual(json.loads(response.content), {"ok": True, "result": "failed"})
        request = self._refresh()
        self.assertEqual(
            (request.status, request.response), ("failed", "judge exploded")
        )
        self.assertIsNone(request.letter)

    def test_invalid_shapes_return_400_and_mark_failed(self):
        match = self._match()
        invalid_payloads = {
            "missing similar_cases": {"request_id": "sim-1"},
            "not a list": self._payload({"case_id": match.pk}),
            "entry not an object": self._payload([match.pk]),
            "case_id string": self._payload(
                [{"case_id": str(match.pk), "score": 0.5, "reason": "r"}]
            ),
            "case_id bool": self._payload(
                [{"case_id": True, "score": 0.5, "reason": "r"}]
            ),
            "score string": self._payload(
                [{"case_id": match.pk, "score": "0.5", "reason": "r"}]
            ),
            "reason missing": self._payload([{"case_id": match.pk, "score": 0.5}]),
            "candidates not a list": self._payload([], candidates={}),
            "problems not a list": self._payload([], problems="p"),
            "more than 3": self._payload(
                [self._entry(self._match()) for _ in range(4)]
            ),
        }
        for label, payload in invalid_payloads.items():
            with self.subTest(label):
                self.similar_request.status = "pending"
                self.similar_request.save()
                response = self._post(payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self._refresh().status, "failed")
                self.assertFalse(
                    Letter.objects.filter(case=self.requesting)
                    .exclude(created_by_is_staff=False)
                    .exists()
                )

    def test_success_keeps_n8n_order_and_stores_data(self):
        older = self._match()
        newer = self._match()
        payload = self._payload(
            [
                self._entry(newer, score=0.71, reason="Pierwsza."),
                self._entry(older, score=0.95, reason="Druga."),
            ],
            problems=[{"problem": "p", "stage": "s", "client_goal": "g"}],
            candidates=[{"case_id": newer.pk, "verdict": "podobna"}],
            judge_fallback=False,
        )

        response = self._post(payload)

        self.assertEqual(
            json.loads(response.content), {"ok": True, "result": "completed"}
        )
        request = self._refresh()
        self.assertEqual(request.status, "completed")
        self.assertEqual(
            request.similar_cases,
            [
                {
                    "case_id": newer.pk,
                    "score": 0.71,
                    "reason": "Pierwsza.",
                    "same_client": False,
                },
                {
                    "case_id": older.pk,
                    "score": 0.95,
                    "reason": "Druga.",
                    "same_client": False,
                },
            ],
        )
        self.assertEqual(
            request.candidates,
            {
                "problems": payload["problems"],
                "candidates": payload["candidates"],
                "judge_fallback": False,
            },
        )
        letter = request.letter
        self.assertEqual(letter.case, self.requesting)
        self.assertEqual(letter.genre, Letter.GENRE.ai_message_staff)
        self.assertEqual(letter.status, Letter.STATUS.staff)
        self.assertEqual(letter.name, "ASYSTENT AI: podobne zamknięte sprawy")
        self.assertTrue(letter.created_by_is_staff)
        self.assertEqual(letter.text, request.response)
        self.assertLess(
            letter.html.index(f"#{newer.pk} "), letter.html.index(f"#{older.pk} ")
        )
        self.assertIn(f'<a href="{newer.get_absolute_url()}">', letter.html)
        self.assertIn(
            "ASYSTENT AI - Podobne zamknięte sprawy "
            "(rodzaj instytucji: Gmina; zakres: DIP)",
            letter.html,
        )
        self.assertIn("Dlaczego podobna:</strong> Pierwsza.", letter.html)
        closed_at = newer.status_changed.date().isoformat()
        self.assertIn(f"Zamknięta:</strong> {closed_at}", letter.html)
        self.assertIn(f"Zamknięta: {closed_at}", letter.text)

    def test_advisor_is_advicer_or_first_staff_with_permission(self):
        from guardian.shortcuts import assign_perm

        with_advicer = self._match()
        with_advicer.advice.advicer = StaffFactory(
            first_name="Jan", last_name="Doradca"
        )
        with_advicer.advice.save()
        tagged_by_bot = self._match()
        tagged_by_bot.advice.advicer = views_module._get_or_create_ai_assistant()
        tagged_by_bot.advice.save()
        staff = StaffFactory(first_name="Anna", last_name="Prawniczka")
        assign_perm("can_view", staff, tagged_by_bot)

        self._post(
            self._payload([self._entry(with_advicer), self._entry(tagged_by_bot)])
        )

        html = self._refresh().letter.html
        self.assertIn("Doradca:</strong> Jan Doradca", html)
        self.assertIn("Doradca:</strong> Anna Prawniczka", html)

    def test_recheck_drops_invalid_cases(self):
        reopened = self._match(status=Case.STATUS.assigned)
        other_kind = self._match(institution_kind=InstitutionKindFactory())
        other_flags = self._match(scope=dip_scope(is_local_government=True))
        valid = self._match()
        cases = [
            ("reopened", reopened.pk),
            ("deleted", 987654),
            ("requesting case", self.requesting.pk),
            ("institution kind changed", other_kind.pk),
            ("scope flags differ", other_flags.pk),
        ]
        for label, case_id in cases:
            with self.subTest(label):
                payload = self._payload(
                    [
                        {"case_id": case_id, "score": 0.9, "reason": "x"},
                        self._entry(valid),
                    ]
                )
                self.assertEqual(self._post(payload).status_code, 200)
                self.assertEqual(
                    [e["case_id"] for e in self._refresh().similar_cases], [valid.pk]
                )

    def test_different_scope_row_with_same_flags_is_kept(self):
        match = self._match(scope=dip_scope(name="Inny zakres DIP"))
        self._post(self._payload([self._entry(match)]))
        self.assertEqual(len(self._refresh().similar_cases), 1)

    def test_same_client_is_flagged(self):
        same = self._match(client=self.requesting.client)
        other = self._match()
        self._post(self._payload([self._entry(same), self._entry(other)]))
        request = self._refresh()
        self.assertEqual(
            [e["same_client"] for e in request.similar_cases], [True, False]
        )
        self.assertEqual(request.letter.html.count("ten sam klient"), 1)
        self.assertIn("Uwaga: ten sam klient", request.letter.text)

    def test_zero_entries_still_create_a_letter(self):
        response = self._post(self._payload([]))
        self.assertEqual(response.status_code, 200)
        letter = self._refresh().letter
        self.assertIsNotNone(letter)
        self.assertIn(
            "Nie znaleziono podobnych zamkniętych spraw dla rodzaju instytucji: "
            "Gmina i zakresu: DIP.",
            letter.html,
        )
        self.assertIn("Nie znaleziono podobnych zamkniętych spraw", letter.text)

    def test_all_entries_dropped_still_create_a_letter(self):
        self._post(self._payload([self._entry(self.requesting)]))
        request = self._refresh()
        self.assertEqual(request.similar_cases, [])
        self.assertIn("Nie znaleziono", request.letter.html)

    def test_ai_tag_sources_are_named_in_the_header(self):
        self.similar_request.institution_kind_source = "ai_tags"
        self.similar_request.scope_source = "ai_tags"
        self.similar_request.save()
        self._post(self._payload([]))
        self.assertIn(
            "(rodzaj instytucji z sugestii AI: Gmina; zakres z sugestii AI: DIP)",
            self._refresh().letter.html,
        )

    def test_values_are_escaped(self):
        match = self._match(name="<script>alert(1)</script>")
        self._post(
            self._payload([self._entry(match, reason='<img src=x onerror="x()">')])
        )
        letter = self._refresh().letter
        self.assertNotIn("<script>", letter.html)
        self.assertNotIn("<img", letter.html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", letter.html)
        self.assertNotIn("<script>", letter.sanitized_html())

    def test_request_without_case_completes_without_letter(self):
        self.similar_request.case = None
        self.similar_request.save()
        response = self._post(self._payload([self._entry(self._match())]))
        self.assertEqual(response.status_code, 200)
        request = self._refresh()
        self.assertEqual(request.status, "completed")
        self.assertIsNone(request.letter)


class SimilarCasesIndexStateAdminTestCase(TestCase):
    def setUp(self):
        self.admin = StaffFactory(is_superuser=True)
        self.client.force_login(self.admin)

    def test_changelist_renders(self):
        state = SimilarCasesIndexState.objects.create(
            case=make_case(), status="error", error="boom"
        )
        response = self.client.get(
            reverse("admin:ai_assistant_similarcasesindexstate_changelist")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, state.case.get_absolute_url())

    def test_change_view_renders_read_only(self):
        state = SimilarCasesIndexState.objects.create(
            case=make_case(), status="error", error="boom"
        )
        response = self.client.get(
            reverse("admin:ai_assistant_similarcasesindexstate_change", args=[state.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "boom")
        self.assertNotContains(response, 'name="error"')

    @patch("poradnia.ai_assistant.admin.sync_case_similar_index_task.delay")
    def test_resync_selected_enqueues_each_row(self, mock_delay):
        first = SimilarCasesIndexState.objects.create(case=make_case(), status="error")
        second = SimilarCasesIndexState.objects.create(case=make_case(), status="empty")
        response = self.client.post(
            reverse("admin:ai_assistant_similarcasesindexstate_changelist"),
            {
                "action": "resync_selected",
                "_selected_action": [first.pk, second.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertCountEqual(
            mock_delay.call_args_list, [call(first.pk), call(second.pk)]
        )

    def test_request_admin_change_view_renders(self):
        request = N8nSimilarCasesRequest.objects.create(
            request_id="sim-admin",
            environment="TEST",
            question="q",
            case=make_case(),
            similar_cases=[{"case_id": 1, "score": 0.5, "reason": "r"}],
            candidates={"problems": [], "candidates": [], "judge_fallback": False},
        )
        changelist = self.client.get(
            reverse("admin:ai_assistant_n8nsimilarcasesrequest_changelist")
        )
        self.assertEqual(changelist.status_code, 200)
        change = self.client.get(
            reverse(
                "admin:ai_assistant_n8nsimilarcasesrequest_change", args=[request.pk]
            )
        )
        self.assertEqual(change.status_code, 200)
        self.assertContains(change, "judge_fallback")

    def test_request_changelist_links_letter_and_handles_missing_case(self):
        letter = LetterFactory(case=make_case())
        N8nSimilarCasesRequest.objects.create(
            request_id="sim-letter",
            environment="TEST",
            question="q",
            case=None,
            letter=letter,
        )
        response = self.client.get(
            reverse("admin:ai_assistant_n8nsimilarcasesrequest_changelist")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, letter.get_absolute_url())


class N8nSimilarCasesRequestAdminExportTestCase(TestCase):
    def setUp(self):
        self.admin = N8nSimilarCasesRequestAdmin(
            N8nSimilarCasesRequest, django_admin.site
        )
        self.request = RequestFactory().get(
            "/admin/ai_assistant/n8nsimilarcasesrequest/"
        )

    def _export(self, obj):
        response = self.admin.export_as_excel(
            self.request, N8nSimilarCasesRequest.objects.filter(pk=obj.pk)
        )
        sheet = openpyxl.load_workbook(BytesIO(response.content)).active
        headers = [cell.value for cell in sheet[1]]
        return headers, dict(zip(headers, [cell.value for cell in sheet[2]]))

    def test_export_includes_pretty_printed_problems_as_last_column(self):
        problems = [{"problem": "p", "stage": "s", "client_goal": "g"}]
        obj = N8nSimilarCasesRequest.objects.create(
            request_id="sim-export-1",
            environment="TEST",
            question="q",
            status="completed",
            similar_cases=[{"case_id": 1, "score": 0.7, "reason": "r"}],
            candidates={
                "problems": problems,
                "candidates": [],
                "judge_fallback": False,
            },
        )

        headers, row = self._export(obj)

        self.assertEqual(headers[-1], "problems")
        self.assertEqual(json.loads(row["problems"]), problems)
        self.assertIn("\n", row["problems"])  # pretty-printed, not compact
        self.assertEqual(
            json.loads(row["similar_cases"]),
            [{"case_id": 1, "score": 0.7, "reason": "r"}],
        )

    def test_export_problems_column_is_blank_when_unset(self):
        obj = N8nSimilarCasesRequest.objects.create(
            request_id="sim-export-2", environment="TEST", question="q"
        )

        _, row = self._export(obj)

        self.assertIsNone(row["problems"])
        self.assertIsNone(row["similar_cases"])

    def test_export_includes_case_link_and_filter_names(self):
        case = make_case()
        obj = N8nSimilarCasesRequest.objects.create(
            request_id="sim-export-3",
            environment="TEST",
            question="q",
            case=case,
            institution_kind=InstitutionKindFactory(name="Sąd"),
            institution_kind_source=N8nSimilarCasesRequest.SOURCE_ADVICE,
            scope=ScopeFactory(name="Dostęp do informacji"),
            scope_source=N8nSimilarCasesRequest.SOURCE_AI_TAGS,
        )

        _, row = self._export(obj)

        self.assertEqual(row["case_id"], case.pk)
        self.assertEqual(
            row["case_absolute_url"],
            self.request.build_absolute_uri(case.get_absolute_url()),
        )
        self.assertEqual(row["institution_kind"], "Sąd")
        self.assertEqual(row["institution_kind_source"], "advice")
        self.assertEqual(row["scope"], "Dostęp do informacji")
        self.assertEqual(row["scope_source"], "ai_tags")
