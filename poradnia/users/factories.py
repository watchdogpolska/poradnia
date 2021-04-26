import string

import factory.fuzzy
from factory.django import DjangoModelFactory


polish_letters = string.ascii_letters
polish_letters += b"\xc4\x85\xc5\xbc\xc5\xba\xc4\x87\xc5\x84\xc3\xb3".decode("utf-8")


class FuzzyPolishText(factory.fuzzy.FuzzyText):
    def __init__(self, prefix="", length=12, suffix="", chars=polish_letters, **kwargs):
        super().__init__(prefix, length, suffix, chars, **kwargs)


class UserFactory(DjangoModelFactory):
    username = factory.Sequence(lambda n: "user%d" % n)
    first_name = FuzzyPolishText()
    last_name = FuzzyPolishText()
    email = factory.LazyAttribute(lambda obj: "%s@example.com" % obj.username)
    password = factory.PostGenerationMethodCall("set_password", "pass")
    picture = factory.django.ImageField()
    codename = factory.Sequence(lambda n: "U_%d" % n)

    class Meta:
        model = "users.User"  # Equivalent to ``model = myapp.models.User``
        django_get_or_create = ("username",)


class StaffFactory(UserFactory):
    is_staff = True


class ProfileFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    description = factory.fuzzy.FuzzyText()
    www = factory.fuzzy.FuzzyText()

    class Meta:
        model = "users.Profile"
