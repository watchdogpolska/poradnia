from django.db import models
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.conf import settings
from model_utils import Choices


class Permission(models.Model):
    case = models.ForeignKey('cases.Case')
    group = models.ForeignKey('LocalGroup')
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

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

    def get_permission_group(self, user):
        return self.case.get_permission_group(user)

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


class LocalGroup(models.Model):
    RANK = Choices('client', 'lawyer', 'student', 'secretary', 'spectator')
    rank = models.CharField(choices=RANK, max_length=15, default=RANK.client)
    group = models.ForeignKey(Group)

    class Meta:
        unique_together = (('rank', 'group',),)

    def __unicode__(self):
        return self.rank
