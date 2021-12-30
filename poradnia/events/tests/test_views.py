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
