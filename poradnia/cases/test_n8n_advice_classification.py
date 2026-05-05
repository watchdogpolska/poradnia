from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from test_plus.test import TestCase

from poradnia.advicer.factories import (
    AreaFactory,
    InstitutionKindFactory,
    IssueFactory,
    PersonKindFactory,
)
from poradnia.cases.factories import CaseFactory, CaseUserObjectPermissionFactory
from poradnia.letters.factories import AttachmentFactory, LetterFactory
from poradnia.users.factories import UserFactory


class CaseN8NAdviceClassificationTestCase(TestCase):
    @override_settings(
        N8N_ADVICE_WEBHOOK_URL="https://n8n.example.test/webhook/advice",
        N8N_ADVICE_WEBHOOK_TOKEN="secret-token",
        N8N_ADVICE_WEBHOOK_TIMEOUT=10,
    )
    @patch("poradnia.cases.models.requests.post")
    def test_request_sends_expected_payload(self, post_mock):
        client = UserFactory(is_staff=False, nicename="Client User")
        advisor = UserFactory(is_staff=True, nicename="Advisor User")
        case = CaseFactory(client=client)

        CaseUserObjectPermissionFactory(
            content_object=case,
            permission_name="can_send_to_client",
            user=advisor,
        )

        first_letter = LetterFactory(
            case=case,
            created_by=client,
            created_by_is_staff=False,
            text="first client letter",
        )
        second_letter = LetterFactory(
            case=case,
            created_by=client,
            created_by_is_staff=False,
            text="second client letter",
        )
        third_letter = LetterFactory(
            case=case,
            created_by=client,
            created_by_is_staff=False,
            text="third client letter should not be sent",
        )
        staff_letter = LetterFactory(
            case=case,
            created_by=advisor,
            created_by_is_staff=True,
            text="staff letter should not be sent",
        )

        first_attachment = AttachmentFactory(
            letter=first_letter,
            text_content="first attachment text",
        )
        second_attachment = AttachmentFactory(
            letter=second_letter,
            text_content="second attachment text",
        )
        AttachmentFactory(letter=third_letter, text_content="third attachment text")
        AttachmentFactory(letter=staff_letter, text_content="staff attachment text")

        issue = IssueFactory(name="Issue active", tag_helper="Issue helper")
        IssueFactory(name="Issue inactive", active=False)
        area = AreaFactory(name="Area active", tag_helper="Area helper")
        person_kind = PersonKindFactory(
            name="Person kind active",
            tag_helper="Person kind helper",
        )
        institution_kind = InstitutionKindFactory(
            name="Institution kind active",
            tag_helper="Institution kind helper",
        )

        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = {"ok": True}
        post_mock.return_value = response_mock

        result = case.request_n8n_advice_classification()

        self.assertEqual(result, {"ok": True})
        response_mock.raise_for_status.assert_called_once()

        post_mock.assert_called_once()
        _, kwargs = post_mock.call_args

        self.assertEqual(
            kwargs["headers"],
            {
                "Authorization": "Bearer secret-token",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(kwargs["timeout"], 10)

        payload = kwargs["json"]

        self.assertEqual(payload["case"], {"id": case.pk, "name": case.name})

        self.assertEqual(
            payload["letters"],
            [
                {
                    "id": first_letter.pk,
                    "text": "first client letter",
                    "attachments": [
                        {
                            "id": first_attachment.pk,
                            "text_content": "first attachment text",
                        }
                    ],
                },
                {
                    "id": second_letter.pk,
                    "text": "second client letter",
                    "attachments": [
                        {
                            "id": second_attachment.pk,
                            "text_content": "second attachment text",
                        }
                    ],
                },
            ],
        )

        self.assertEqual(
            payload["issues"],
            [{"id": issue.pk, "name": "Issue active", "tag_helper": "Issue helper"}],
        )
        self.assertEqual(
            payload["areas"],
            [{"id": area.pk, "name": "Area active", "tag_helper": "Area helper"}],
        )
        self.assertEqual(
            payload["person_kinds"],
            [
                {
                    "id": person_kind.pk,
                    "name": "Person kind active",
                    "tag_helper": "Person kind helper",
                }
            ],
        )
        self.assertEqual(
            payload["institution_kinds"],
            [
                {
                    "id": institution_kind.pk,
                    "name": "Institution kind active",
                    "tag_helper": "Institution kind helper",
                }
            ],
        )
        self.assertEqual(
            payload["client"],
            {"id": client.pk, "name": client.get_nicename()},
        )
        self.assertEqual(
            payload["advisor"],
            {"id": advisor.pk, "name": advisor.get_nicename()},
        )

    @override_settings(
        N8N_ADVICE_WEBHOOK_URL="https://n8n.example.test/webhook/advice",
        N8N_ADVICE_WEBHOOK_TOKEN="secret-token",
    )
    @patch("poradnia.cases.models.requests.post")
    def test_request_returns_text_for_non_json_response(self, post_mock):
        case = CaseFactory()

        response_mock = Mock()
        response_mock.status_code = 202
        response_mock.text = "accepted"
        response_mock.json.side_effect = ValueError
        post_mock.return_value = response_mock

        result = case.request_n8n_advice_classification()

        self.assertEqual(result, {"status_code": 202, "text": "accepted"})
        response_mock.raise_for_status.assert_called_once()

    @override_settings(N8N_ADVICE_WEBHOOK_URL="", N8N_ADVICE_WEBHOOK_TOKEN="")
    def test_request_requires_settings(self):
        case = CaseFactory()

        with self.assertRaises(ImproperlyConfigured):
            case.request_n8n_advice_classification()
