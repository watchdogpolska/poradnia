import factory
import factory.fuzzy
from cases.models import Case, PermissionGroup
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from users.factories import UserFactory


class CaseFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    client = factory.SubFactory(UserFactory)
    created_by = factory.LazyAttribute(lambda obj: obj.client)

    class Meta:
        model = Case


class PermissionGroupFactory(factory.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            ct = ContentType.objects.get_for_model(Case)
            permissions = Permission.objects.filter(codename__in=extracted,
                                                    content_type=ct).all()
            for permission in permissions:
                self.permissions.add(permission)

    class Meta:
        model = PermissionGroup
