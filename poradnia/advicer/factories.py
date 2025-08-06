import datetime

import factory
import factory.fuzzy


class IssueFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "issue-%d" % n)

    class Meta:
        model = "advicer.Issue"


class AreaFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "area-%d" % n)

    class Meta:
        model = "advicer.Area"


class PersonKindFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "person-kind-%d" % n)

    class Meta:
        model = "advicer.PersonKind"


class InstitutionKindFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "institution-kind-%d" % n)

    class Meta:
        model = "advicer.InstitutionKind"


class AdviceFactory(factory.django.DjangoModelFactory):
    advicer = factory.SubFactory("poradnia.users.factories.UserFactory")
    grant_on = factory.fuzzy.FuzzyDateTime(
        datetime.datetime(2008, 1, 1, tzinfo=datetime.timezone.utc)
    )
    created_by = factory.SubFactory("poradnia.users.factories.UserFactory")
    comment = factory.Sequence("advice-comment-{}".format)
    subject = factory.Sequence("advice-subject-{}".format)
    visible = True

    class Meta:
        model = "advicer.Advice"
