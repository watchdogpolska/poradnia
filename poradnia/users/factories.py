import string

import factory.fuzzy

polish_letters = string.ascii_letters
polish_letters += b"\xc4\x85\xc5\xbc\xc5\xba\xc4\x87\xc5\x84\xc3\xb3".decode("utf-8")


class FuzzyPolishText(factory.fuzzy.FuzzyText):
    def __init__(self, prefix="", length=12, suffix="", chars=polish_letters, **kwargs):
        super().__init__(prefix, length, suffix, chars, **kwargs)


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: "user%d" % n)
    first_name = FuzzyPolishText()
    last_name = FuzzyPolishText()
    email = factory.LazyAttribute(lambda obj: "%s@example.com" % obj.username)
    password = factory.PostGenerationMethodCall("set_password", "pass")
    # Every instance otherwise gets the same default filename
    # ("example.jpg"), so storage's collision-avoidance kicks in for every
    # user after the first and appends a non-seedable random suffix
    # (Django's get_available_name() uses a CSPRNG, immune to
    # random.seed()) - that made the avatar path, and therefore the
    # sorl-thumbnail cache path derived from it, different on every single
    # run regardless of environment. Keying the filename to the (unique,
    # deterministic) username avoids the collision entirely.
    picture = factory.django.ImageField(
        filename=factory.LazyAttribute(lambda o: "%s.jpg" % o.factory_parent.username)
    )
    codename = factory.Sequence(lambda n: "U_%d" % n)

    class Meta:
        model = "users.User"  # Equivalent to ``model = myapp.models.User``
        django_get_or_create = ("username",)

    @factory.post_generation
    def profile(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted is False:
            # Don't create a profile if it will be auto-created
            return
        # Only create a profile if extracted is a dict with extra fields
        if isinstance(extracted, dict):
            ProfileFactory(user=self, **extracted)


class StaffFactory(UserFactory):
    is_staff = True


class ProfileFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    description = factory.Sequence("profile-description-{}".format)
    www = factory.Sequence("profile-www-{}".format)

    class Meta:
        model = "users.Profile"
