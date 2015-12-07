import factory


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.LazyAttribute(lambda obj: '%s@example.com' % obj.username)
    password = factory.PostGenerationMethodCall('set_password', 'pass')
    picture = factory.django.ImageField()
    codename = factory.Sequence(lambda n: 'U_%d' % n)

    class Meta:
        model = 'users.User'  # Equivalent to ``model = myapp.models.User``
        django_get_or_create = ('username', )


class StaffFactory(UserFactory):
    is_staff = True
