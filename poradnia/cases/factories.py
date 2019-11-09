from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
import factory
import factory.fuzzy

from poradnia.cases.models import Case, PermissionGroup, CaseUserObjectPermission
from poradnia.users.factories import UserFactory


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
            permissions = Permission.objects.filter(
                codename__in=extracted, content_type=ct
            ).all()
            for permission in permissions:
                self.permissions.add(permission)

    class Meta:
        model = PermissionGroup


class CaseUserObjectPermissionFactory(factory.DjangoModelFactory):
    content_object = factory.SubFactory(CaseFactory)
    user = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def permission(self):
        content_type = ContentType.objects.get_for_model(self.content_object)
        return Permission.objects.get(
            codename=self.permission_name, content_type=content_type
        )

    class Params:
        permission_name = "can_send_to_client"

    class Meta:
        model = CaseUserObjectPermission
