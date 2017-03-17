from django.test import TestCase
from django.utils import timezone

from poradnia.cases.factories import CaseFactory
from poradnia.events.factories import EventFactory
from poradnia.events.models import Event, Reminder
from poradnia.users.factories import UserFactory, ProfileFactory


def create_event():
    Event.objects.create()


class RemindersTestCase(TestCase):

    def setUp(self):
        self.staff_user = UserFactory(is_staff=True)
        ProfileFactory(user=self.staff_user)
        self.regular_user = UserFactory()
        ProfileFactory(user=self.regular_user)

        self.regular_case = CaseFactory(created_by=self.regular_user)
        self.staff_case = CaseFactory(created_by=self.staff_user)

    def test_not_create_reminder_for_regular_user(self):
        self.assertFalse(Reminder.objects.exists())
        _ = EventFactory(case=self.regular_case)
        self.assertFalse(Reminder.objects.exists())

    def test_create_reminder_for_staff_user(self):
        self.assertFalse(Reminder.objects.exists())
        new_event = EventFactory(case=self.staff_case)

        new_reminder = Reminder.objects.first()

        self.assertIsNotNone(new_reminder)
        self.assertEqual(new_reminder.user, self.staff_user)
        self.assertEqual(new_reminder.event, new_event)

    def test_not_create_reminder_for_staff_user_without_profile(self):
        staff_user_no_profile = UserFactory(is_staff=True)
        case = CaseFactory(created_by=staff_user_no_profile)
        self.assertFalse(Reminder.objects.exists())
        _ = EventFactory(case=case)
        self.assertFalse(Reminder.objects.exists())

    def test_not_create_reminder_for_staff_user_with_disabled_reminders(self):
        staff_user = UserFactory(is_staff=True)
        ProfileFactory(user=staff_user)
        staff_user.profile.event_reminder_time = 0
        staff_user.profile.save()

        case = CaseFactory(created_by=staff_user)
        self.assertFalse(Reminder.objects.exists())
        _ = EventFactory(case=case)
        self.assertFalse(Reminder.objects.exists())

    def test_not_create_reminder_if_no_deadline(self):
        self.assertFalse(Reminder.objects.exists())
        _ = EventFactory(case=self.staff_case, deadline=False)
        self.assertFalse(Reminder.objects.exists())

    def test_reset_reminder_if_event_date_was_modified(self):
        self.assertFalse(Reminder.objects.exists())
        new_event = EventFactory(case=self.staff_case)
        reminder = Reminder.objects.first()

        self.assertFalse(reminder.triggered)

        # force trigger
        reminder.triggered = True
        reminder.save()
        self.assertTrue(reminder.triggered)

        # edit event
        new_event.time = timezone.now()
        new_event.save()

        # ensure value is reset
        reminder.refresh_from_db()
        self.assertFalse(reminder.triggered)

    def test_not_reset_reminder_if_other_event_field_was_changed(self):
        self.assertFalse(Reminder.objects.exists())
        new_event = EventFactory(case=self.staff_case)
        reminder = Reminder.objects.first()

        self.assertFalse(reminder.triggered)

        # force trigger
        reminder.triggered = True
        reminder.save()
        self.assertTrue(reminder.triggered)

        # edit event
        new_event.text = "Totally new text"
        new_event.save()

        # ensure value is NOT reset
        reminder.refresh_from_db()
        self.assertTrue(reminder.triggered)
