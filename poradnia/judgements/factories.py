import datetime

import factory.fuzzy
from factory.django import DjangoModelFactory
from django.utils.timezone import now

from poradnia.cases.factories import CaseFactory
from poradnia.events.factories import EventFactory
from poradnia.judgements.models import SessionRow
from poradnia.judgements.registry import get_parser_keys
from poradnia.users.factories import UserFactory


class CourtFactory(DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    parser_key = factory.Iterator(get_parser_keys())

    class Meta:
        model = "judgements.Court"


class CourtCaseFactory(DjangoModelFactory):
    court = factory.SubFactory(CourtFactory)
    case = factory.SubFactory(CaseFactory)
    signature = factory.Sequence("IV/Waw {}/2015".format)
    created_by = factory.SubFactory(UserFactory)

    class Meta:
        model = "judgements.CourtCase"


class CourtSessionFactory(DjangoModelFactory):
    courtcase = factory.SubFactory(CourtCaseFactory)
    event = factory.SubFactory(EventFactory)
    parser_key = factory.Iterator(get_parser_keys())

    class Meta:
        model = "judgements.CourtSession"


DESCRIPTION_PATTERN = "Sequanece:{n}\nSignature:{signature}\nTime:{datetime}"


class SessionRowFactory(factory.Factory):
    signature = factory.Sequence("IV/Waw {}/2015".format)
    datetime = factory.Sequence(lambda n: now() - datetime.timedelta(days=n))

    @factory.lazy_attribute_sequence
    def description(self, n):
        return DESCRIPTION_PATTERN.format(
            n=n,
            signature=self.signature,
            datetime=self.datetime.strftime("%Y-%M-%D %h-%m"),
        )

    class Meta:
        model = SessionRow
