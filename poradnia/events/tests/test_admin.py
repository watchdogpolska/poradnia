from atom.mixins import AdminTestCaseMixin
from test_plus import TestCase

from poradnia.events.factories import EventFactory
from poradnia.events.models import Event
from poradnia.users.factories import UserFactory


class EventAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = EventFactory
    model = Event
