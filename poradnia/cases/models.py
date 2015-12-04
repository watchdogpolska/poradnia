from re import match

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q, Count
from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase
from guardian.shortcuts import assign_perm, get_users_with_perms
from model_utils import Choices
from model_utils.fields import MonitorField, StatusField
from model_utils.managers import PassThroughManager

from cases.tags.models import Tag
from template_mail.utils import send_tpl_email


class CaseQuerySet(QuerySet):

    def for_user(self, user):
        if user.has_perm('cases.can_view_all'):
            return self
        content_type = ContentType.objects.get_for_model(Case)
        return self.filter(caseuserobjectpermission__permission__codename='can_view',
                           caseuserobjectpermission__permission__content_type=content_type,
                           caseuserobjectpermission__user=user)

    def with_perm(self):
        return self.prefetch_related('caseuserobjectpermission_set')

    def with_record_count(self):
        return self.annotate(record_count=Count('record'))

    def by_involved_in(self, user, by_user=True, by_group=False):
        condition = Q()
        if by_user:
            condition = condition | Q(caseuserobjectpermission__user=user)
        if by_group:
            condition = condition | Q(casegroupobjectpermission__group__user=user)
        return self.filter(condition)

    def by_msg(self, message):
        cond = Q()
        # Assosiate by email
        for email in message.to_addresses:
            import re
            result = re.match('^sprawa-(?P<pk>\d+)@porady.siecobywatelska.pl$', email)
            if result:
                cond = cond | Q(pk=result.group('pk'))
        if not cond.children:
            return self.none()
        return self.filter(cond)


class Case(models.Model):
    STATUS = Choices(('0', 'free', _('free')),
                     ('1', 'assigned', _('assigned')),
                     ('2', 'closed', _('closed'))
                     )
    name = models.CharField(max_length=150, verbose_name=_("Subject"))
    tags = models.ManyToManyField(Tag, null=True, blank=True, verbose_name=_("Tags"))
    status = StatusField()
    status_changed = MonitorField(monitor='status')
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='case_client', verbose_name=_("Client"))
    letter_count = models.IntegerField(default=0, verbose_name=_("Letter count"))
    last_send = models.DateTimeField(null=True, blank=True, verbose_name=_("Last send"))
    last_action = models.DateTimeField(null=True, blank=True, verbose_name=_("Last action"))
    deadline = models.ForeignKey('events.Event',
                                 null=True,
                                 blank=True,
                                 related_name='event_deadline', verbose_name=_("Dead-line"))
    objects = PassThroughManager.for_queryset_class(CaseQuerySet)()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="case_created", verbose_name=_("Created by"))
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_("Created on"))
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                    related_name="case_modified", verbose_name=_("Modified by"))
    modified_on = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name=_("Modified on"))
    handled = models.BooleanField(default=False, verbose_name=_("Handled"))

    def status_display(self):
        return self.STATUS[self.status]

    def get_readed(self):
        try:
            obj = self.readed_set.all()[0]
        except IndexError:
            return False
        if obj.user.is_staff and self.last_action and self.last_action > obj.time:
            return False
        if not obj.user.is_staff and self.last_send and self.last_send > obj.time:
            return False
        return True

    def get_absolute_url(self):
        return reverse('cases:detail', kwargs={'pk': str(self.pk)})

    def get_edit_url(self):
        return reverse('cases:edit', kwargs={'pk': str(self.pk)})

    def get_users_with_perms(self, *args, **kwargs):
        return get_users_with_perms(self, with_group_users=False, *args, **kwargs)

    def __unicode__(self):
        return self.name

    def get_email(self):
        return settings.PORADNIA_EMAIL_OUTPUT % self.__dict__

    @classmethod
    def get_by_email(cls, email):
        filter_param = match(settings.PORADNIA_EMAIL_INPUT, email)
        if not filter_param:
            raise cls.DoesNotExist
        return cls.objects.get(**filter_param.groupdict())

    # TODO: Remove
    def perm_check(self, user, perm):
        if not (user.has_perm('cases.' + perm) or user.has_perm('cases.' + perm, self)):
            raise PermissionDenied
        return True

    # TODO: Remove
    def view_perm_check(self, user):
        if not (user.has_perm('cases.can_view_all') or user.has_perm('cases.can_view', self)):
            raise PermissionDenied
        return True

    class Meta:
        ordering = ['last_send', ]
        permissions = (('can_view_all', _("Can view all cases")),  # Global permission
                       ('can_view', _("Can view")),
                       ('can_select_client', _("Can select client")),  # Global permission
                       ('can_assign', _("Can assign new permissions")),
                       ('can_send_to_client', _("Can send text to client")),
                       ('can_manage_permission', _("Can assign permission")),
                       ('can_add_record', _('Can add record')),
                       ('can_change_own_record', _("Can change own records")),
                       ('can_change_all_record', _("Can change all records")),
                       )

    def update_handled(self):
        from letters.models import Letter
        try:
            obj = Letter.objects.case(self).filter(status='done').last()
            if obj.created_by.is_staff:
                self.handled = True
            else:
                self.handled = False
        except IndexError:
            self.handled = False
        self.save()

    def update_counters(self, save=True):
        from letters.models import Letter
        letters_list = Letter.objects.case(self)
        self.letter_count = letters_list.count()
        try:
            last_action = letters_list.last()
            self.last_action = last_action.created_on
        except IndexError:
            pass

        try:
            last_send = letters_list.last_staff_send()
            self.last_send = last_send.status_changed or last_send.created_on
        except IndexError:
            self.last_send = None

        try:
            self.deadline = self.event_set.filter(deadline=True).order_by('time').all()[0]
        except IndexError:
            self.deadline = None
        if save:
            self.save()

    def status_update(self, reopen=False, save=True):
        if self.status == self.STATUS.closed and not reopen:
            return False
        content_type = ContentType.objects.get_for_model(Case)
        qs = CaseUserObjectPermission.objects.filter(permission__codename='can_send_to_client',
                                                     permission__content_type=content_type,
                                                     content_object=self,
                                                     user__is_staff=True)
        check = qs.exists()
        self.status = self.STATUS.assigned if check else self.STATUS.free
        if save:
            self.save()

    def assign_perm(self):
        assign_perm('can_view', self.created_by, self)  # assign creator
        assign_perm('can_add_record', self.created_by, self)  # assign creator
        if self.created_by.has_perm('cases.can_send_to_client'):
            assign_perm('can_send_to_client', self.created_by, self)
        if self.created_by != self.client:
            assign_perm('can_view', self.client, self)  # assign client
            assign_perm('can_add_record', self.client, self)  # assign client

    # TODO: Remove
    def send_notification(self, actor, target=None, staff=None, **context):
        qs = self.get_users_with_perms().exclude(pk=actor.pk)
        if staff is not None:
            qs = qs.filter(is_staff=staff)
        if target is None:
            target = self
        for user in qs:
            user.notify(actor=actor,
                        target=target,
                        from_email=self.get_email(),
                        **context)


class CaseUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Case)

    def save(self, *args, **kwargs):
        super(CaseUserObjectPermission, self).save(*args, **kwargs)
        if self.permission.codename == 'can_send_to_client':
            self.content_object.status = self.content_object.STATUS.assigned
            self.content_object.save()

    def delete(self, *args, **kwargs):
        super(CaseUserObjectPermission, self).delete(*args, **kwargs)
        self.content_object.status_update()


class CaseGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Case)


limit = {'content_type__app_label': 'cases', 'content_type__name': 'case'}


class PermissionGroup(models.Model):
    name = models.CharField(max_length=25,
                            verbose_name=_("Name"))
    permissions = models.ManyToManyField(Permission,
                                         verbose_name=_("Permissions"),
                                         limit_choices_to=limit)

    def __unicode__(self):
        return self.name


def notify_new_case(sender, instance, created, **kwargs):
    if created:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
        except ImportError:
            from django.contrib.auth.models import User

        content_type = ContentType.objects.get_for_model(Case)
        users = User.objects.filter(user_permissions__codename='can_view_all',
                                    user_permissions__content_type=content_type).all()
        email = [x.email for x in users]
        send_tpl_email('cases/email/case_new.html',
                       recipient_list=email,
                       context={'case': instance})

post_save.connect(notify_new_case, sender=Case, dispatch_uid="new_case_notify")


def assign_perm_new_case(sender, instance, created, **kwargs):
    if created:
        instance.assign_perm()

post_save.connect(assign_perm_new_case, sender=Case, dispatch_uid="assign_perm_new_case")
