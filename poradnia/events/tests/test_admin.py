from test_plus import TestCase

from atom.mixins import AdminTestCaseMixin
from poradnia.events.factories import EventFactory, AlarmFactory
from poradnia.events.models import Event, Alarm
from poradnia.users.factories import UserFactory


class EventAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = EventFactory
    model = Event


class AlarmAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = AlarmFactory
    model = Alarm
