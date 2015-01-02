from django.db import models
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from model_utils.fields import MonitorField, StatusField
from model_utils import Choices
from django.db.models.query import QuerySet
from model_utils.managers import PassThroughManager


class Style(models.Model):
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=30, unique=True)


class Tag(models.Model):
    site = models.ForeignKey(Site)
    style = models.ForeignKey(Style)
    name = models.CharField(max_length=10)


class Permission(models.Model):
    case = models.ForeignKey('Case')
    rank = models.ForeignKey(Group)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    def get_update_msg(self):
        context = {}
        context['user'] = self.user
        context['case'] = self.case
        context['rank'] = self.rank
        return render_to_string('cases/permission_msg.html', context)

    def get_update_title(self):
        context = {}
        context['user'] = self.user
        context['case'] = self.case
        context['rank'] = self.rank
        return render_to_string('cases/permission_msg_title.html', context)

    def __unicode__(self):
        return "%s as %s for %s" % (self.user.username, self.rank.name, self.case.name)

    def get_permission_group(self, user):
        return self.rank

    def save(self, *args, **kwargs):
        from letters.models import Letter
        from tracking.models import Following
        is_new = True if self.pk is None else False
        super(Permission, self).save(*args, **kwargs)
        if is_new:
            Following(user=self.user, case=self.case).save()
        Letter(name=self.get_update_title(), comment=self.get_update_msg(), case=self.case).save()


class SiteGroup(models.Model):
    RANK = Choices('client', 'lawyer', 'student', 'secretary', 'spectator')
    site = models.ForeignKey(Site)
    rank = models.CharField(choices=RANK, max_length=15, default=RANK.client)
    group = models.ForeignKey(Group)

    @classmethod
    def for_current(cls):
        return cls.objects.filter(site=Site.objects.get_current())


class CaseQuerySet(QuerySet):
    def for_user(self, user):
        if user.has_perm('cases.can_view_all'):  # All rank can view own cases
            return self
        field = 'permission__user_id'  # Mam obawy czy to nie jest zbyt wiele relacji...
        return self.filter(**{field: user.pk})

    def without_lawyers(self):
        group = SiteGroup.for_current().get(rank=SiteGroup.RANK.lawyer)
        return self.exclude(permission__rank=group).all()


class Case(models.Model):
    STATUS = Choices('open', 'closed')
    name = models.CharField(max_length=250)
    tags = models.ManyToManyField(Tag, null=True, blank=True)
    status = StatusField()
    status_changed = MonitorField(monitor='status')
    client = models.ForeignKey(settings.AUTH_USER_MODEL)
    objects = PassThroughManager.for_queryset_class(CaseQuerySet)()

    def get_absolute_url(self):
        return reverse('cases:detail', kwargs={'pk': str(self.pk)})

    def get_edit_url(self):
        return reverse('cases:edit', kwargs={'pk': str(self.pk)})

    def __unicode__(self):
        return self.name

    def get_permission_group(self, user):
        return self.permission_set.get(user=user).rank

    def get_lawyers(self):
        group = SiteGroup.for_current().get(rank=SiteGroup.RANK.lawyer)
        return (c.user for c in self.permission_set.filter(rank=group).all())

    def save(self, *args, **kwargs):
        is_new = (True if self.pk is None else False)
        super(Case, self).save(*args, **kwargs)
        if is_new:
            self.assign(self.client, SiteGroup.RANK.client)

    def assign(self, user, rank=SiteGroup.RANK.client):
        site = Site.objects.get_current()  # TODO: As manager of SiteGroup
        group = SiteGroup.objects.get(site=site, rank=rank).group
        return Permission(case=self, rank=group, user=user).save()

    class Meta:
        permissions = (("can_select_client", "Can select client"),
                       ('can_view_all', "Can view all cases"))
