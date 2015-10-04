import factory
import factory.fuzzy

from users.factories import UserFactory


class CaseFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    client = factory.SubFactory(UserFactory)
    created_by = factory.LazyAttribute(lambda obj: obj.client)

    class Meta:
        model = 'cases.Case'
