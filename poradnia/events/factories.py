from datetime import timedelta

from django.utils import timezone
import factory.fuzzy

from poradnia.cases.factories import CaseFactory
from poradnia.users.factories import UserFactory


class EventFactory(factory.django.DjangoModelFactory):
    text = factory.fuzzy.FuzzyText()
    deadline = True
    time = factory.fuzzy.FuzzyDateTime(timezone.now())
    created_by = factory.SubFactory(UserFactory)
    created_on = factory.fuzzy.FuzzyDateTime(timezone.now() - timedelta(hours=5))
    case = factory.SubFactory(CaseFactory)

    class Meta:
        model = "events.Event"


class ReminderFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)

    class Meta:
        model = "events.Reminder"
