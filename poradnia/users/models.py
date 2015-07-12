# -*- coding: utf-8 -*-
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet
from django.db.models import Count
from django.contrib.auth.models import UserManager
from django.utils import timezone
from django.template.loader import render_to_string
from guardian.mixins import GuardianUserMixin
from model_utils.managers import PassThroughManager
from template_mail.utils import send_tpl_email
import notifications

USERNAME = _('Username')  # Hack to overwrite django translation


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
            username = "user-%s" % (User.objects.count(), )  # TOOD: Race cognition
            user = self.model(username=username, email=email,
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

    def get_nicename(self):
        if self.first_name or self.last_name:
            return "{0} {1}".format(self.first_name, self.last_name)
        return self.username

    def __unicode__(self):
        text = self.get_nicename()
        if self.is_staff:
            text += ' (team)'
        return text

    def send_tpl_email_user(self, template_name, context, from_email, **kwds):
        return send_tpl_email(template_name, self.email, context, from_email, **kwds)

    def notify(self, actor, verb, target, from_email=None):
        notifications.notify.send(actor, verb=verb, target=target, recipient=self)
        template_name = '%s/email/%s_%s.txt' % (target._meta.app_label, target._meta.model_name, verb)
        context = dict(actor=actor, verb=verb, target=target, recipient=self)
        if from_email:
            context['email'] = from_email
        return self.send_tpl_email_user(template_name, context, "%s <%s>" % (actor, from_email))

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})

    class Meta:
        permissions = (("can_view_other", "Can view other"),)
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class Profile(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    description = models.TextField(blank=True, verbose_name=_("Description"))
    www = models.URLField(null=True, blank=True, verbose_name=_("Homepage"))

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")
