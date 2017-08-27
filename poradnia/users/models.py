# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Case, Count, F, Func, IntegerField, Q, When
from django.db.models.query import QuerySet
from django.utils.encoding import python_2_unicode_compatible
from django.utils.datetime_safe import datetime
from django.utils.translation import ugettext_lazy as _
from guardian.mixins import GuardianUserMixin
from guardian.utils import get_anonymous_user
from model_utils.choices import Choices
from sorl.thumbnail import ImageField

from poradnia.cases.models import Case as CaseModel
from poradnia.template_mail.utils import send_tpl_email

_('Username or e-mail')  # Hack to overwrite django translation
_('Login')


class UserQuerySet(QuerySet):
    def for_user(self, user):
        if not user.has_perm('users.can_view_other'):
            return self.filter(Q(pk=user.pk) | Q(is_staff=True))
        return self

    def with_case_count(self):
        return self.annotate(case_count=Count('case_client', distinct=True))

    def with_case_count_assigned(self):
        free = Count(
            Case(
                When(caseuserobjectpermission__content_object__status=CaseModel.STATUS.free,
                     then='caseuserobjectpermission__content_object__pk'),
                default=None,
                output_field=IntegerField()),
            distinct=True)

        active = Count(
            Case(
                When(caseuserobjectpermission__content_object__status=CaseModel.STATUS.assigned,
                     then='caseuserobjectpermission__content_object__pk'),
                default=None,
                output_field=IntegerField()),
            distinct=True)

        closed = Count(
            Case(
                When(caseuserobjectpermission__content_object__status=CaseModel.STATUS.closed,
                     then='caseuserobjectpermission__content_object__pk'),
                default=None,
                output_field=IntegerField()),
            distinct=True)

        return self.annotate(case_assigned_sum=free + active + closed,
                             case_assigned_free=free,
                             case_assigned_active=active,
                             case_assigned_closed=closed)

    def registered(self):
        user = get_anonymous_user()
        return self.exclude(pk=user.pk)

    def with_month_year(self):
        return self.annotate(
            month=Func(F('created_on'),
                       function='month',
                       output_field=IntegerField())
        ).annotate(
            year=Func(F('created_on'),
                      function='year',
                      output_field=IntegerField())
        )

    def active(self):
        start = datetime.today().replace(day=1)
        return self.filter(
            letter_created_by__created_on__date__gte=start
        ).annotate(active=Count('letter_created_by'))


class CustomUserManager(UserManager.from_queryset(UserQuerySet)):
    def get_by_email_or_create(self, email, notify=True):
        try:
            user = self.model.objects.get(email=email)  # Support allauth EmailAddress
        except self.model.DoesNotExist:
            user = self.register_email(email=email, notify=notify)
        return user

    def email_to_unique_username(self, email, limit=10):
        suffix_len = len(str(limit)) + 1
        max_length = User._meta.get_field('username').max_length - suffix_len
        limit_org = limit
        prefix = re.sub(r'[^A-Za-z-]', '_', email)
        prefix = prefix[:max_length]
        if not User.objects.filter(username=prefix).exists():
            return prefix
        while limit > 0:
            username = "{prefix}-{no}".format(prefix=prefix, no=limit_org - limit + 1)
            if not User.objects.filter(username=username).exists():
                return username
            limit -= 1
        raise ValueError("This email are completly creapy. I am unable to generate username")

    def register_email(self, email, notify=True, **extra_fields):
        email = self.normalize_email(email)
        password = self.make_random_password()
        username = self.email_to_unique_username(email)
        user = self.create_user(username, email, password)
        if notify:
            context = {'user': user, 'password': password}
            send_tpl_email(template_name='users/email_new_user.html',
                           recipient_list=[email],
                           context=context)
        return user


@python_2_unicode_compatible
class User(GuardianUserMixin, AbstractUser):
    picture = ImageField(upload_to='avatars', verbose_name=_("Avatar"), null=True, blank=True)
    codename = models.CharField(max_length=15, null=True, blank=True, verbose_name=_("Codename"))
    created_on = models.DateTimeField(auto_now_add=True,
                                      null=True,
                                      blank=True,
                                      verbose_name=_("Created on"))
    objects = CustomUserManager()

    def get_codename(self):
        return self.codename or self.get_nicename()

    def get_nicename(self):
        if self.first_name or self.last_name:
            return self.get_full_name()
        return self.username

    def __str__(self):
        text = self.get_nicename()
        if self.is_staff:
            text += ' (team)'
        return text

    def send_template_email(self, template_name, context=None, from_email=None, **kwds):
        return send_tpl_email(template_name=template_name,
                              recipient_list=[self.email],
                              context=context or {},
                              from_email=from_email,
                              **kwds)

    def _get_notify_template_name(self, target, verb):
        return '%s/email/%s_%s.txt' % (target._meta.app_label, target._meta.model_name, verb)

    def _get_email_name(self, actor, from_email):
        if from_email:
            return u"%s <%s>" % (actor, from_email)
        return None

    def notify(self, actor, verb, **kwargs):
        notify_kw = {'sender': actor,
                     'verb': verb,
                     # 'object': kwargs.get('object', None),
                     # 'target': kwargs.get('target', None),
                     }
        # send(recipient=self, **notify_kw)

        if 'target' not in kwargs:
            return

        template_name = self._get_notify_template_name(kwargs['target'], verb)
        from_email = kwargs.get('from_email', None)

        email_name = self._get_email_name(actor, from_email)

        context = kwargs
        context['email'] = from_email  # TODO: Drop this alias
        context['actor'] = actor
        return self.send_template_email(template_name, context, email_name)

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})

    class Meta:
        ordering = ['pk', ]
        permissions = (("can_view_other", "Can view other"),)
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class Profile(models.Model):
    EVENT_REMINDER_CHOICE = Choices(
        (0, "no_reminder", _("No reminder")),
        (1, "one_day", _("1 day")),
        (3, "three_days", _("3 days")),
        (7, "seven_days", _("7 days")),
    )
    user = models.OneToOneField(User, primary_key=True)
    description = models.TextField(blank=True, verbose_name=_("Description"))
    www = models.URLField(null=True, blank=True, verbose_name=_("Homepage"))
    email_footer = models.TextField(null=True, blank=True, verbose_name=_("Email footer"))
    event_reminder_time = models.IntegerField(
        choices=EVENT_REMINDER_CHOICE, default=EVENT_REMINDER_CHOICE.one_day,
        verbose_name=_("Event Reminder Time")
    )

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")
