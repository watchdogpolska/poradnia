import datetime

from django.utils.timezone import utc
import factory
import factory.fuzzy
from factory.django import DjangoModelFactory


class IssueFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "issue-%d" % n)

    class Meta:
        model = "advicer.Issue"


class AreaFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "area-%d" % n)

    class Meta:
        model = "advicer.Area"


class PersonKindFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "person-kind-%d" % n)

    class Meta:
        model = "advicer.PersonKind"


class InstitutionKindFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "institution-kind-%d" % n)

    class Meta:
        model = "advicer.InstitutionKind"


class AdviceFactory(DjangoModelFactory):
    advicer = factory.SubFactory("poradnia.users.factories.UserFactory")
    grant_on = factory.fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=utc))
    created_by = factory.SubFactory("poradnia.users.factories.UserFactory")
    comment = factory.fuzzy.FuzzyText()
    subject = factory.fuzzy.FuzzyText()
    visible = True

    class Meta:
        model = "advicer.Advice"
