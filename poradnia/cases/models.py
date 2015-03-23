from re import match
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Count, Q
from django.db.models.query import QuerySet
from model_utils.managers import PassThroughManager
from model_utils.fields import MonitorField, StatusField
from model_utils import Choices
from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase
from guardian.shortcuts import get_objects_for_user, get_users_with_perms, assign_perm
from django.core.exceptions import PermissionDenied
from notifications import notify
from .tags.models import Tag


class CaseQuerySet(QuerySet):
    def for_user(self, user):
        if user.has_perm('cases.can_view_all'):
            return self
        return get_objects_for_user(user, 'cases.can_view', self, any_perm=True)

    def with_read_time(self, user):
        return self.prefetch_related('readed_set').filter(readed__user=user)

    def with_record_count(self):
        return self.annotate(record_count=Count('record'))

    def by_involved_in(self, user, by_user=True, by_group=False):
        condition = Q()
        if by_user:
            condition = condition | Q(caseuserobjectpermission__user=user)
        if by_group:
            condition = condition | Q(casegroupobjectpermission__group__user=user)
        return self.filter(condition)


class Case(models.Model):
    STATUS = Choices('free', 'open', 'closed')
    name = models.CharField(max_length=150)
    tags = models.ManyToManyField(Tag, null=True, blank=True)
    status = StatusField()
    status_changed = MonitorField(monitor='status')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='case_client')
    letter_count = models.IntegerField(default=0)
    last_send = models.DateTimeField(null=True, blank=True)
    last_action = models.DateTimeField(null=True, blank=True)
    deadline = models.ForeignKey('events.Event',
        null=True,
        blank=True,
        related_name='event_deadline')
    objects = PassThroughManager.for_queryset_class(CaseQuerySet)()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="case_created")
    created_on = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
        related_name="case_modified")
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)

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

    def get_permission_url(self):
        return reverse('cases:permission', kwargs={'pk': str(self.pk)})

    def get_users_with_perms(self, *args, **kwargs):
        return get_users_with_perms(self, *args, **kwargs)

    def __unicode__(self):
        return self.name

    def get_email(self):
        return 'case-{0}@poradnia.siecobywatelska.pl'.format(self.pk)

    def get_by_email(self, email):
        pk = match('^case-([0-9]+)@poradnia.siecobywatelska.pl$', email)
        if not pk:
            raise self.DoesNotExist
        return self.objects.get(pk=pk.group(1))

    def perm_check(self, user, perm):
        if not user.has_perm('cases.' + perm):
            raise PermissionDenied
        return True

    def view_perm_check(self, user, perm='VIEW'):
        if not (user.has_perm('cases.can_view_all') or
                user.has_perm('cases.can_view', self)):
                raise PermissionDenied
        return True

    class Meta:
        ordering = ['last_send', ]
        permissions = (('can_view_all', "Can view all cases",),  # Global permission
                       ('can_view', "Can view",),
                       ('can_select_client', "Can select client"),  # Global permission
                       ('can_assign', "Can assign new permissions"),
                       ('can_send_to_client', "Can send text to client"),
                       ('can_manage_permission', "Can assign permission",),
                       ('can_add_record', 'Can add record', ),
                       ('can_change_own_record', "Can change own records"),
                       ('can_change_all_record', "Can change all records"),
                       )

    def update_counters(self, save=True):
        from letters.models import Letter
        letters_list = Letter.objects.filter(record__case=self)
        self.letter_count = letters_list.count()
        try:
            last_action = letters_list.order_by('-created_on', '-id').all()[0]
            self.last_action = last_action.created_on
        except IndexError:
            pass

        try:
            last_send = letters_list.filter(status='done').order_by('-created_on', '-id').all()[0]
            self.last_send = last_send.status_changed or last_send.created_on
        except IndexError:
            pass

        try:
            self.deadline = self.event_set.order_by('time').all()[0]
        except IndexError:
            pass
        if save:
            self.save()

    def assign_perm(self):
        assign_perm('can_view', self.created_by, self)  # assign creator
        assign_perm('can_add_record', self.created_by, self)  # assign creator
        if self.created_by != self.client:
            assign_perm('can_view', self.client, self)  # assign client
            assign_perm('can_add_record', self.client, self)  # assign client

    def send_notification(self, actor, verb):
        for user in self.get_users_with_perms().exclude(pk=actor.pk):
            notify.send(actor, target=self, verb=verb, recipient=user)

    def save(self, *args, **kwargs):
        created = True if self.pk is None else False
        super(Case, self).save(*args, **kwargs)
        if created:
            self.assign_perm()


class CaseUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Case)


class CaseGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Case)
