from django.db import models
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.db.models.query import QuerySet
from django.conf import settings
from model_utils import Choices
from model_utils.managers import PassThroughManager


class PermissionQuerySet(QuerySet):
    def for_user(self, user):
        print user.has_perm('cases.can_view_all')
        if user.has_perm('cases.can_view_all'):  # All rank can view own cases
            return self
        field = 'permission__user'
        return self.filter(**{field: user})


class Permission(models.Model):
    case = models.ForeignKey('cases.Case')
    group = models.ForeignKey('LocalGroup')
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    objects = PassThroughManager.for_queryset_class(PermissionQuerySet)()

    def get_update_msg(self):
        context = {}
        context['user'] = self.user
        context['case'] = self.case
        context['group'] = self.group
        return render_to_string('permissions/permission_msg.html', context)

    def get_update_title(self):
        context = {}
        context['user'] = self.user
        context['case'] = self.case
        context['group'] = self.group
        return render_to_string('permissions/permission_msg_title.html', context)

    def __unicode__(self):
        return "%s as %s for %s" % (self.user.username, self.group.rank, self.case.name)

    def get_permissions_set(self, user):
        return self.case.get_permissions_set(user)

    def save(self, *args, **kwargs):
        from letters.models import Letter
        from tracking.models import Following
        is_new = True if self.pk is None else False
        super(Permission, self).save(*args, **kwargs)
        if is_new:
            Following(user=self.user, case=self.case).save()
        Letter(name=self.get_update_title(), comment=self.get_update_msg(), case=self.case).save()

    class Meta:
        unique_together = (('user', 'case',),)
        permissions = (("can_delete_own_permission", "Can delete own permission"),
                       )


class LocalGroup(models.Model):
    RANK = Choices('client', 'lawyer', 'student', 'secretary', 'spectator')
    rank = models.CharField(choices=RANK, max_length=15, default=RANK.client)
    group = models.ForeignKey(Group)

    class Meta:
        unique_together = (('rank', 'group',),)

    def __unicode__(self):
        return self.rank
