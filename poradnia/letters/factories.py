import factory
import factory.fuzzy
from factory.django import ImageField

from poradnia.cases.factories import CaseFactory
from poradnia.users.factories import UserFactory


class LetterFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence("letter-name-{}".format)
    text = factory.Sequence("letter-text-{}".format)
    signature = factory.Sequence("letter-signature-{}".format)
    created_by = factory.SubFactory(UserFactory)
    genre = "mail"
    status = "done"
    created_by_is_staff = factory.LazyAttribute(lambda obj: obj.created_by.is_staff)
    eml = ImageField()
    case = factory.SubFactory(CaseFactory)

    class Meta:
        model = "letters.Letter"


class AttachmentFactory(factory.django.DjangoModelFactory):
    letter = factory.SubFactory(LetterFactory)
    attachment = ImageField()

    class Meta:
        model = "letters.Attachment"
