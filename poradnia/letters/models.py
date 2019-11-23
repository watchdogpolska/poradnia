import logging

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from os.path import basename
from django.conf import settings
from django.db import models
from django.db.models import F, Func, IntegerField, Q
from django.utils.translation import ugettext_lazy as _
from django_mailbox.models import Message
from model_utils import Choices
from model_utils.fields import MonitorField, StatusField

from poradnia.cases.models import Case
from poradnia.cases.utils import get_users_with_perm
from poradnia.records.models import AbstractRecord, AbstractRecordQuerySet
from poradnia.users.models import User

from .utils import date_random_path

from django.urls import reverse

logger = logging.getLogger(__name__)


class LetterQuerySet(AbstractRecordQuerySet):
    def for_user(self, user):
        qs = super().for_user(user)
        if not user.is_staff:
            qs = qs.filter(status=Letter.STATUS.done)
        return qs

    def last_staff_send(self):
        return (
            self.filter(status="done", created_by__is_staff=True)
            .order_by("-created_on", "-id")
            .all()[0]
        )

    def last_received(self):
        return (
            self.filter(created_by__is_staff=False)
            .order_by("-created_on", "-id")
            .all()[0]
        )

    def last(self):
        return self.order_by("-created_on", "-id").all()[0]

    def case(self, case):
        return self.filter(record__case=case)

    def with_month_year(self):
        return self.annotate(
            month=Func(F("created_on"), function="month", output_field=IntegerField())
        ).annotate(
            year=Func(F("created_on"), function="year", output_field=IntegerField())
        )


class Letter(AbstractRecord):
    STATUS = Choices(("staff", _("Staff")), ("done", _("Done")))
    GENRE = Choices("mail", "comment")
    genre = models.CharField(choices=GENRE, default=GENRE.comment, max_length=20)
    status = StatusField(db_index=True)
    status_changed = MonitorField(monitor="status")
    accept = MonitorField(
        monitor="status", when=["done"], verbose_name=_("Accepted on")
    )
    name = models.CharField(max_length=250, verbose_name=_("Subject"))
    text = models.TextField(verbose_name=_("Text"))
    html = models.TextField(verbose_name=_("HTML"), blank=True)
    signature = models.TextField(verbose_name=_("Signature"), blank=True, null=True)
    created_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="letter_created_by",
        verbose_name=_("Created by"),
        on_delete=models.CASCADE,
    )
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_("Created on"))
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Modified by"),
        null=True,
        on_delete=models.CASCADE,
        related_name="letter_modified_by",
    )
    modified_on = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name=_("Modified on")
    )
    message = models.ForeignKey(
        to=Message, null=True, blank=True, on_delete=models.CASCADE
    )
    eml = models.FileField(
        _("Raw message contents"),
        null=True,
        upload_to="messages",
        help_text=_("Original full content of message"),
    )

    objects = LetterQuerySet.as_manager()

    def __str__(self):
        return self.name

    def get_users(self, force_all=False):
        users_to_notify = self.get_users_with_perms()

        if self.status == self.STATUS.staff or force_all:
            users_to_notify = users_to_notify.filter(is_staff=True)

        return users_to_notify

    def get_absolute_url(self):
        case_url = self.record.case_get_absolute_url()
        return "{}#letter-{}".format(case_url, self.pk)

    def is_done(self):
        return True if self.status == self.STATUS.done else False

    def is_html(self):
        return bool(self.html)

    def render_as_html(self):
        if self.is_html():
            return self.html
        else:
            return "<pre>{text}</pre>".format(text=self.text)

    def get_edit_url(self):
        return reverse("letters:edit", kwargs={"pk": self.pk})

    def get_send_url(self):
        return reverse("letters:send", kwargs={"pk": self.pk})

    def set_new_case(self):
        self.case = Case.objects.create(
            subject=self.name, created_by=self.created_by, client=self.client
        )

    def send_notification(self, *args, **kwargs):
        staff_users = get_users_with_perm(self.case, "can_send_to_client")
        management = User.objects.filter(notify_unassigned_letter=True).all()
        if self.status is Letter.STATUS.done:
            if len(list(staff_users)) > 0:
                kwargs["user_qs"] = self.get_users_with_perms()
            else:
                kwargs["user_qs"] = User.objects.filter(
                    Q(pk__in=self.get_users_with_perms()) | Q(pk__in=management)
                )
        else:
            if len(list(staff_users)) > 0:
                kwargs["user_qs"] = self.get_users_with_perms().filter(is_staff=True)
            else:
                kwargs["user_qs"] = User.objects.filter(
                    Q(pk__in=self.get_users_with_perms().filter(is_staff=True))
                    | Q(pk__in=management)
                )
        return super().send_notification(*args, **kwargs)

    class Meta:
        verbose_name = _("Letter")
        verbose_name_plural = _("Letters")
        ordering = ["-created_on"]


lrc_cup = "letter__record__case__caseuserobjectpermission"


class AttachmentQuerySet(models.QuerySet):
    def for_user(self, user):
        qs = self
        if not user.has_perm("cases.can_view_all"):
            content_type = ContentType.objects.get_for_model(Case)
            qs = qs.filter(
                **{
                    "{}__permission__codename".format(lrc_cup): "can_view",
                    "{}__permission__content_type".format(lrc_cup): content_type,
                    "{}__user".format(lrc_cup): user,
                }
            )
        if not user.is_staff:
            qs = qs.filter(letter__status=Letter.STATUS.done)
        return qs


class Attachment(models.Model):
    letter = models.ForeignKey(to=Letter, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to=date_random_path, verbose_name=_("File"))

    objects = AttachmentQuerySet.as_manager()

    @property
    def filename(self):
        return basename(self.attachment.name)

    def __str__(self):
        return "%s" % (self.filename)

    def get_absolute_url(self):
        return self.attachment.url

    def get_full_url(self):
        return "".join(
            ["https://", get_current_site(None).domain, self.get_absolute_url()]
        )

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")
