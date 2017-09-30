from atom.mixins import AdminTestCaseMixin
from test_plus import TestCase

from poradnia.events.factories import AlarmFactory, EventFactory
from poradnia.events.models import Alarm, Event
from poradnia.users.factories import UserFactory


class EventAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = EventFactory
    model = Event


class AlarmAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = AlarmFactory
    model = Alarm
