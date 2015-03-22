# -*- coding: utf-8 -*-
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet
from django.db.models import Count
from django.contrib.auth.models import UserManager
from django.utils import timezone
from django.template.loader import render_to_string
from guardian.mixins import GuardianUserMixin
from model_utils.managers import PassThroughManager


class UserQuerySet(QuerySet):
    def for_user(self, user):
        if not user.has_perm('users.can_view_other'):
            return self.filter(Q(username=user.username) | Q(is_staff=True))
        return self

    def with_case_count(self):
        return self.annotate(case_count=Count('case'))


class CustomUserManager(GuardianUserMixin, PassThroughManager.for_queryset_class(UserQuerySet),
        UserManager):
    def get_by_email_or_create(self, email, notify=True, **extra_fields):
        try:
            user = self.model.objects.get(email=email)  # Support allauth EmailAddress
        except self.model.DoesNotExist:
            now = timezone.now()
            email = self.normalize_email(email)
            password = self.make_random_password()
            user = self.model(username=email, email=email,
                              is_staff=False, is_active=True,
                              is_superuser=False, date_joined=now,
                              **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            text = render_to_string('users/email_new_user.html',
                {'user': user, 'password': password})
            user.email_user('New registration', text)
        return user


class User(AbstractUser):
    objects = CustomUserManager()

    def __unicode__(self):

        if self.first_name or self.last_name:
            text = "{0} {1}".format(self.first_name, self.last_name)
        text = self.username
        if self.is_staff:
            text += ' (team)'
        return text

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})

    class Meta:
        permissions = (("can_view_other", "Can view other"),)
