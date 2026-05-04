import datetime
import json

from atom.ext.guardian.tests import PermissionStatusMixin
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from poradnia.cases.factories import CaseFactory
from poradnia.events.factories import EventFactory
from poradnia.events.models import Event
from poradnia.users.factories import UserFactory


class EventCreateViewTestCase(PermissionStatusMixin, TestCase):
    permission = ["cases.can_add_record"]

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="john")
        self.case = self.permission_object = CaseFactory()
        self.url = reverse("events:add", kwargs={"case_pk": self.case.pk})

    def test_create_event(self):
        self.login_permitted_user()
        response = self.client.post(
            self.url, {"deadline": "yes", "time": "2017-01-20 11:00", "text": "Skarga"}
        )
        self.assertEqual(response.status_code, 302)
        event = Event.objects.get()
        self.assertEqual(event.text, "Skarga")
        valid_time = timezone.now().replace(2017, 1, 20, 10, 00)
        self.assertEqual(event.time.date(), valid_time.date())
        self.assertEqual(event.time.hour, valid_time.hour)
        self.assertEqual(event.time.minute, valid_time.minute)
        self.assertEqual(event.deadline, True)


class EventUpdateViewTestCase(PermissionStatusMixin, TestCase):
    permission = ["cases.can_add_record"]

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="john")
        self.event = EventFactory()
        self.permission_object = self.event.case
        self.url = reverse("events:edit", kwargs={"pk": self.event.pk})

    def test_update_event(self):
        self.assertTrue(Event.objects.all().exists())

        self.login_permitted_user()
        response = self.client.post(
            self.url, {"deadline": False, "time": "2017-01-20 11:00", "text": "Skarga"}
        )
        self.assertEqual(response.status_code, 302)

        event = Event.objects.get()
        self.assertEqual(event.text, "Skarga")
        valid_time = timezone.now().replace(2017, 1, 20, 10, 00)
        self.assertEqual(event.time.date(), valid_time.date())
        self.assertEqual(event.time.hour, valid_time.hour)
        self.assertEqual(event.time.minute, valid_time.minute)
        self.assertEqual(event.deadline, False)


class EventAjaxDatatableViewTestCase(TestCase):
    """Regression coverage for issue #2200.

    A POST that includes ``date_from`` / ``date_to`` used to assert-fail inside
    ``ajax_datatable`` because ``get_latest_by`` returned a column name that
    wasn't in ``column_defs``.
    """

    COLUMN_NAMES = [
        "time",
        "text",
        "case_name",
        "case_client",
        "properties",
        "court_case",
        "court",
    ]

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username="ajax-staff", is_superuser=True, is_staff=True)
        cls.case = CaseFactory()
        cls.event = EventFactory(
            case=cls.case,
            time=timezone.make_aware(datetime.datetime(2025, 6, 15, 12, 0)),
        )
        cls.url = reverse("events:events_table_ajax_data")

    def _build_payload(self, **overrides):
        payload = {
            "draw": "1",
            "start": "0",
            "length": "20",
            "search[value]": "",
            "search[regex]": "false",
            "order[0][column]": "0",
            "order[0][dir]": "desc",
        }
        for index, name in enumerate(self.COLUMN_NAMES):
            payload[f"columns[{index}][data]"] = name
            payload[f"columns[{index}][name]"] = name
            payload[f"columns[{index}][searchable]"] = "true"
            payload[f"columns[{index}][orderable]"] = "true"
            payload[f"columns[{index}][search][value]"] = ""
            payload[f"columns[{index}][search][regex]"] = "false"
        payload.update(overrides)
        return payload

    def test_date_range_filter_returns_200_not_500(self):
        """Posting ``date_from``/``date_to`` must not 500 — see #2200."""
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            self._build_payload(date_from="2020-01-01", date_to="2030-12-31"),
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertIn("recordsTotal", body)
        self.assertIn("data", body)

    def test_date_from_only_returns_200(self):
        """A single ``date_from`` (no ``date_to``) must also not 500."""
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            self._build_payload(date_from="2020-01-01"),
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertIn("recordsTotal", body)
