import factory
import factory.fuzzy

from users.factories import UserFactory
from cases.factories import CaseFactory


class LetterFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    text = factory.fuzzy.FuzzyText()
    signature = factory.fuzzy.FuzzyText()
    created_by = factory.SubFactory(UserFactory)
    status = 'done'

    case = factory.SubFactory(CaseFactory)

    class Meta:
        model = 'letters.Letter'
