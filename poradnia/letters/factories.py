import factory
import factory.fuzzy
from factory.django import ImageField

from poradnia.cases.factories import CaseFactory
from poradnia.users.factories import UserFactory


class LetterFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    text = factory.fuzzy.FuzzyText()
    signature = factory.fuzzy.FuzzyText()
    created_by = factory.SubFactory(UserFactory)
    status = "done"

    case = factory.SubFactory(CaseFactory)

    class Meta:
        model = "letters.Letter"


class AttachmentFactory(factory.django.DjangoModelFactory):
    letter = factory.SubFactory(LetterFactory)
    attachment = ImageField()

    class Meta:
        model = "letters.Attachment"
