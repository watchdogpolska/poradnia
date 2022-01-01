from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

from poradnia.cases.models import Case


class RecordQuerySet(QuerySet):
    def _for_user_by_view(self, user):
        if user.has_perm("cases.can_view_all"):
            return self
        content_type = ContentType.objects.get_for_model(Case)
        return self.filter(
            case__caseuserobjectpermission__permission__codename="can_view",
            case__caseuserobjectpermission__permission__content_type=content_type,
            case__caseuserobjectpermission__user=user,
        )

    def for_user(self, user):
        qs = self._for_user_by_view(user)
        if user.is_staff:
            return qs
        return qs.filter(Q(event=None) & Q(letter__status="done"))

    def move(self, target):
        for field in Record.STATIC_RELATION + ["courtcase"]:
            qs = self.filter(**{f"{field}__isnull": False}).values_list(
                field, flat=True
            )
            Record._meta.get_field(field).related_model.objects.filter(
                pk__in=qs
            ).update(case=target)
        return self.update(case=target)


class Record(models.Model):
    STATIC_RELATION = ["letter", "event"]
    case = models.ForeignKey(to="cases.Case", on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    letter = models.OneToOneField(
        to="letters.Letter", on_delete=models.CASCADE, null=True, blank=True
    )
    event = models.OneToOneField(
        to="events.Event", null=True, blank=True, on_delete=models.CASCADE
    )
    courtcase = models.OneToOneField(
        to="judgements.CourtCase", null=True, blank=True, on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        to=ContentType, null=True, blank=True, on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField(null=True)
    related_object = GenericForeignKey("content_type", "object_id")

    objects = RecordQuerySet.as_manager()

    @property  # We use OneToOneField as possible
    def content_object(self):
        for field in self.STATIC_RELATION:
            if getattr(self, field + "_id"):
                return getattr(self, field)
        return self.related_object

    @content_object.setter
    def content_object(self, obj):
        for field in self.STATIC_RELATION:
            if self._meta.get_field(field).related_model == obj._meta.model:
                setattr(self, field, obj)
        self.related_object = obj

    def get_users_with_perms(self, *args, **kwargs):
        return Case(pk=self.case_id).get_users_with_perms()

    def case_get_absolute_url(self):
        return Case(pk=self.case_id).get_absolute_url()

    class Meta:
        ordering = ["created_on", "id"]
        verbose_name = _("Record")
        verbose_name_plural = _("Records")


class AbstractRecordQuerySet(QuerySet):
    def for_user(self, user):
        if user.has_perm("cases.can_view_all"):
            return self
        content_type = ContentType.objects.get_for_model(Case)
        return self.filter(
            case__caseuserobjectpermission__permission__codename="can_view",
            case__caseuserobjectpermission__permission__content_type=content_type,
            case__caseuserobjectpermission__user=user,
        )


class AbstractRecord(models.Model):
    record_general = GenericRelation(to="records.Record", related_query_name="record")
    case = models.ForeignKey(to=Case, on_delete=models.CASCADE)

    def show_modifier(self):
        return self.modified_by_id and self.modified_by_id != self.created_by_id

    def get_users_with_perms(self, *args, **kwargs):
        return self.case.get_users_with_perms(*args, **kwargs)

    def get_template_list(self):
        return "{}/_{}_list.html".format(self._meta.app_label, self._meta.model_name)

    def send_notification(self, *args, **kwargs):
        return self.case.send_notification(target=self, *args, **kwargs)

    def save(self, *args, **kwargs):
        created = True if self.pk is None else False
        super().save(*args, **kwargs)
        if created:
            record = Record(case=self.case)
            record.content_object = self
            record.save()
        self.case.update_counters()

    def __str__(self):
        return _("{object_name} (#{pk}) in case #{case_id}").format(
            object_name=self._meta.verbose_name, case_id=self.case_id, pk=self.pk
        )

    class Meta:
        abstract = True
