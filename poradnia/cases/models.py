import itertools
import logging
import re
from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import models
from django.db.models import (
    BooleanField,
    CharField,
    Count,
    F,
    Func,
    IntegerField,
    Prefetch,
    Q,
    expressions,
)
from django.db.models.functions import Cast
from django.db.models.query import QuerySet
from django.db.models.signals import post_save, pre_delete
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase
from guardian.shortcuts import assign_perm, get_objects_for_user, get_users_with_perms
from model_utils import Choices
from model_utils.fields import MonitorField, StatusField

from poradnia.template_mail.utils import TemplateKey, TemplateMailManager
from poradnia.utils.constants import NAME_MAX_LENGTH
from poradnia.utils.mixins import FormattedDatetimeMixin, UserPrettyNameMixin
from poradnia.utils.utils import get_numeric_param

# TODO: move to settings and fix for DEV and DEMO modes
CASE_PK_RE = r"sprawa-(?P<pk>\d+)@porady.siecobywatelska.pl"


logger = logging.getLogger(__name__)


def delete_files_for_cases(cases):
    from poradnia.letters.models import Attachment, Letter

    def delete_qs(qs, field):
        for x in qs:
            if not getattr(x, field):
                continue
            getattr(x, field).delete()

    delete_qs(Attachment.objects.filter(letter__case__in=cases), "attachment")
    delete_qs(Letter.objects.filter(case__in=cases), "eml")


class CaseQuerySet(FormattedDatetimeMixin, UserPrettyNameMixin, QuerySet):
    def for_assign(self, user):
        return self.filter(
            caseuserobjectpermission__user=user,
            caseuserobjectpermission__permission__codename="can_view",
        )

    def for_user(self, user):
        return get_objects_for_user(user, "can_view", self)

    def with_perm(self):
        return self.prefetch_related("caseuserobjectpermission_set")

    def with_record_count(self):
        return self.annotate(record_count=Count("record"))

    def with_involved_staff(self):
        qs = (
            CaseUserObjectPermission.objects.filter(user__is_staff=True)
            .select_related("permission", "user")
            .all()
        )
        return self.prefetch_related(
            Prefetch("caseuserobjectpermission_set", queryset=qs)
        )

    def involved_staff(self):
        involved_staff_ids = set(
            CaseUserObjectPermission.objects.filter(user__is_staff=True)
            .select_related("permission", "user")
            .values_list("user", flat=True)
            .all()
        )
        qs = (
            get_user_model()
            .objects.filter(id__in=involved_staff_ids)
            .order_by("nicename")
        )
        return qs

    def by_involved_in(self, user, by_user=True, by_group=False):
        condition = Q()
        if by_user:
            condition = condition | Q(caseuserobjectpermission__user=user)
        if by_group:
            condition = condition | Q(casegroupobjectpermission__group__user=user)
        return self.filter(condition)

    def by_msg(self, message):
        envelope = message.get_email_object().get(
            "Envelope-To"
        ) or message.get_email_object().get("To")
        if not envelope:
            return self.none()

        result = re.search(CASE_PK_RE, envelope)

        if not result:
            return self.none()
        return self.filter(pk=result.group("pk"))

    def by_addresses(self, addresses):
        pks = [
            re.match(CASE_PK_RE, address).group("pk")
            for address in addresses
            if re.match(CASE_PK_RE, address)
        ]
        return self.filter(pk__in=pks)

    def order_for_user(self, user, is_next):
        order = "" if is_next else "-"
        if user.is_staff:
            field_name = self.model.STAFF_ORDER_DEFAULT_FIELD
        else:
            field_name = self.model.USER_ORDER_DEFAULT_FIELD
        return self.order_by(
            "{}{}".format(order, field_name), "{}{}".format(order, "pk")
        )

    def with_month_year(self):
        return self.annotate(
            month=Func(F("created_on"), function="month", output_field=IntegerField())
        ).annotate(
            year=Func(F("created_on"), function="year", output_field=IntegerField())
        )

    def with_advice_status(self):
        return self.annotate(advice_count=Count("advice")).annotate(
            has_advice=expressions.Case(
                expressions.When(advice_count=0, then=False),
                default=True,
                output_field=BooleanField(),
            )
        )

    def with_formatted_deadline(self):
        return self.annotate(
            # TODO add explicit datetime formatting with TZ for MySql
            deadline_str=Cast("deadline__time", output_field=CharField())
        )

    def area_filter(self, jst):
        return self.filter(
            advice__jst__tree_id=jst.tree_id,
            advice__jst__lft__range=(jst.lft, jst.rght),
        )

    def ajax_boolean_filter(self, request, prefix, field):
        filter_values = []
        for choice in [("yes", True), ("no", False)]:
            filter_name = prefix + choice[0]
            if get_numeric_param(request, filter_name):
                filter_values.append(choice[1])
        if filter_values:
            return self.filter(**{field + "__in": filter_values})
        else:
            return self.filter(**{field + "__isnull": True})

    def ajax_status_filter(self, request):
        choices = Case.STATUS._identifier_map
        filter_values = []
        for choice in choices.keys():
            filter_name = "status_" + choice.lower()
            if get_numeric_param(request, filter_name):
                filter_values.append(choices[choice])
        if filter_values:
            return self.filter(status__in=filter_values)
        else:
            return self.filter(status__isnull=True)

    def ajax_involved_staff_filter(self, request):
        involved_staff_filter = get_numeric_param(request, "involved_staff_filter")
        if involved_staff_filter:
            involved = get_user_model().objects.filter(id=involved_staff_filter).first()
            return self.by_involved_in(user=involved).distinct()
        return self

    def ajax_has_deadline_filter(self, request):
        # to provide empty queryset when none of the options is selected
        deadline_query = Q(deadline=0)
        # build query for deadline according to user selection
        for choice in [("yes", False), ("no", True)]:
            filter_name = "has_deadline_" + choice[0]
            if get_numeric_param(request, filter_name):
                deadline_query |= Q(deadline__isnull=choice[1])
        return self.filter(deadline_query)

    def old_cases_to_delete(self):
        years_to_store = settings.YEARS_TO_STORE_CASES
        current_month = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        oldest_date = current_month + relativedelta(years=-years_to_store)
        return self.filter(last_action__lt=oldest_date)


class Case(models.Model):
    STAFF_ORDER_DEFAULT_FIELD = "last_action"
    USER_ORDER_DEFAULT_FIELD = "last_send"
    STATUS = Choices(
        ("0", "free", _("free")),
        ("3", "moderated", _("moderated")),
        ("1", "assigned", _("assigned")),
        ("2", "closed", _("closed")),
    )
    STATUS_STYLE = {
        "0": "far fa-circle ",
        "1": "far fa-circle-dot",
        "3": "far fa-square-plus",
        "2": "fas fa-circle",
    }
    id = models.AutoField(verbose_name=_("Case number"), primary_key=True)
    name = models.CharField(max_length=NAME_MAX_LENGTH, verbose_name=_("Subject"))
    status = StatusField()
    status_changed = MonitorField(monitor="status")
    client = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="case_client",
        on_delete=models.CASCADE,
        verbose_name=_("Client"),
    )
    letter_count = models.IntegerField(default=0, verbose_name=_("Letter count"))
    last_send = models.DateTimeField(null=True, blank=True, verbose_name=_("Last send"))
    last_action = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last action")
    )
    last_received = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last received")
    )
    deadline = models.ForeignKey(
        to="events.Event",
        null=True,
        blank=True,
        related_name="event_deadline",
        on_delete=models.CASCADE,
        verbose_name=_("Dead-line"),
    )
    objects = CaseQuerySet.as_manager()
    created_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="case_created",
        verbose_name=_("Created by"),
        on_delete=models.CASCADE,
    )
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_("Created on"))
    modified_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        related_name="case_modified",
        verbose_name=_("Modified by"),
    )
    modified_on = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name=_("Modified on")
    )
    handled = models.BooleanField(default=False, verbose_name=_("Handled"))
    has_project = models.BooleanField(default=False, verbose_name=_("Has project"))

    def status_display(self):
        return self.STATUS[self.status]

    def get_absolute_url(self):
        return reverse("cases:detail", kwargs={"pk": str(self.pk)})

    def render_case_link(self):
        url = self.get_absolute_url()
        label = self.name
        bold_start = "" if self.handled else "<b>"
        bold_end = "" if self.handled else "</b>"
        return f'{bold_start}<a href="{url}">{label}</a>{bold_end}'

    def render_case_link_formatted(self, user):
        url = self.get_absolute_url()
        label = self.name
        template_string = """
            {% load cases_tags %}
            <span class="{{ object.status|status2css }}">
                {% if user.is_staff and not object.handled %}<b>{% endif %}
                <a href="{{ url }}">{{ label }}</a>
                {% if user.is_staff and not object.handled %}</b>{% endif %}
            </span>"""
        template = Template(template_string)
        context = Context({"object": self, "url": url, "label": label, "user": user})
        return template.render(context=context)

    def render_status(self):
        status_icon = self.STATUS_STYLE[self.status]
        return f'<span class="{status_icon}"></span>'

    def render_project_badge(self):
        if self.has_project:
            title = _("Reply to client to remove badge")
            name = _("Project")
            return f"""
                <span class="label label-success" title="{title}">
                <i class="fas fa-pencil"></i> {name}
                </span>
            """
        else:
            return ""

    def render_handled(self):
        if not self.handled:
            return '<span class="fas fa-check"></span>'
        else:
            return ""

    def render_involved_staff(self):
        permissions = self.caseuserobjectpermission_set.all()
        grouped_permissions = itertools.groupby(permissions, lambda p: p.user)
        user_list = [
            {
                "grouper": key,
                "title": ", ".join([p.permission.name for p in list(group)]),
            }
            for key, group in grouped_permissions
            if key.is_staff
        ]
        return "<br>".join(
            [
                f"""
                <span class="label label-info" title="{user["title"]}">
                {user["grouper"].get_nicename()}</span>
            """
                for user in user_list
            ]
        )

    def render_case_advice_link(self):
        try:
            return self.advice.render_advice_link()
        except ObjectDoesNotExist:
            return ""

    def get_edit_url(self):
        return reverse("cases:edit", kwargs={"pk": str(self.pk)})

    def get_close_url(self):
        return reverse("cases:close", kwargs={"pk": str(self.pk)})

    def get_users_with_perms(self, *args, **kwargs):
        return get_users_with_perms(self, with_group_users=False, *args, **kwargs)

    def __str__(self):
        return self.name

    def get_email(self):
        return settings.PORADNIA_EMAIL_OUTPUT % self.__dict__

    # TODO: Remove
    def perm_check(self, user, perm):
        if not (user.has_perm("cases." + perm) or user.has_perm("cases." + perm, self)):
            raise PermissionDenied
        return True

    class Meta:
        ordering = ["last_send"]
        verbose_name = _("Case")
        verbose_name_plural = _("Cases")
        permissions = (
            ("can_view", _("Can view")),
            ("can_assign", _("Can assign new permissions")),
            ("can_send_to_client", _("Can send text to client")),
            ("can_manage_permission", _("Can assign permission")),
            ("can_add_record", _("Can add record")),
            ("can_change_own_record", _("Can change own records")),
            ("can_change_all_record", _("Can change all records")),
            ("can_close_case", _("Can close case")),
            ("can_merge_case", _("Can merge case")),
            # Global permission
            ("can_select_client", _("Can select client")),
        )

    def update_handled(self):
        from poradnia.letters.models import Letter

        try:
            obj = Letter.objects.case(self).filter(status="done").last()
            if obj.created_by.is_staff:
                self.handled = True
            else:
                self.handled = False
        except IndexError:
            self.handled = False
        self.save()

    def update_counters(self, save=True):
        from poradnia.letters.models import Letter

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
            last_received = letters_list.last_received()
            self.last_received = last_received.created_on
        except IndexError:
            self.last_received = None

        try:
            self.deadline = (
                self.event_set.filter(deadline=True)
                .filter(time__gte=timezone.now())
                .order_by("time")
                .all()[0]
            )
        except IndexError:
            self.deadline = None

        if save:
            self.save()

    def update_status(self, reopen=False, save=True):
        if reopen or (self.status != self.STATUS.closed):
            if self.has_assignees():
                self.status = self.STATUS.assigned
            elif self.has_team():
                self.status = self.STATUS.moderated
            else:
                self.status = self.STATUS.free
        if save:
            self.save()

    def has_team(self):
        """
        Checks if there exists a staff member who has a permission to handle
        the case.
        """
        content_type = ContentType.objects.get_for_model(Case)
        qs = CaseUserObjectPermission.objects.filter(
            permission__content_type=content_type,
            content_object=self,
            user__is_staff=True,
        )
        return qs.exists()

    def has_assignees(self):
        """
        Checks if there exists a staff member who has a permission to handle
        the case.
        """
        content_type = ContentType.objects.get_for_model(Case)
        qs = CaseUserObjectPermission.objects.filter(
            permission__codename="can_send_to_client",
            permission__content_type=content_type,
            content_object=self,
            user__is_staff=True,
        )
        return qs.exists()

    def assign_perm(self):
        assign_perm("can_view", self.created_by, self)  # assign creator
        assign_perm("can_add_record", self.created_by, self)  # assign creator
        if self.created_by.has_perm("cases.can_send_to_client"):
            assign_perm("can_send_to_client", self.created_by, self)
        if self.created_by != self.client:
            assign_perm("can_view", self.client, self)  # assign client
            assign_perm("can_add_record", self.client, self)  # assign client

    # TODO: Remove
    def send_notification(self, actor, user_qs, target=None, **context):
        if target is None:
            target = self
        users_to_notify = user_qs
        User = get_user_model()
        if not settings.NOTIFY_AUTHOR:
            users_to_notify = User.objects.exclude(pk=actor.pk).distinct() & user_qs
        logger.info(
            f"Case: {self.id} - sending notification "
            f"to author: {settings.NOTIFY_AUTHOR}"
        )
        for user in users_to_notify:
            user.notify(
                actor=actor, target=target, from_email=self.get_email(), **context
            )
            logger.info(f"Notification sent to {user} with {context}")

    def close(self, actor, notify=True):
        self.modified_by = actor
        self.status = self.STATUS.closed
        if notify:
            self.send_notification(
                actor=actor, user_qs=self.get_users_with_perms(), verb="closed"
            )

    def get_next_for_user(self, user, **kwargs):
        return self.get_next_or_prev_for_user(is_next=True, user=user)

    def get_prev_for_user(self, user, **kwargs):
        return self.get_next_or_prev_for_user(is_next=False, user=user)

    def get_next_or_prev_for_user(self, is_next, user, **kwargs):
        op = "gt" if is_next else "lt"
        if user.is_staff:
            field_name = self.STAFF_ORDER_DEFAULT_FIELD
        else:
            field_name = self.USER_ORDER_DEFAULT_FIELD
        param = getattr(self, field_name)
        q = Q()
        if param:
            q = q | Q(**{"{}__{}".format(field_name, op): param})
        if self.pk:
            q = q | Q(**{field_name: param, "pk__%s" % op: self.pk})
        manager = self.__class__._default_manager.using(self._state.db).filter(**kwargs)
        qs = manager.filter(q)
        qs = qs.order_for_user(user=user, is_next=is_next)
        qs = qs.for_user(user)

        try:
            return qs[0]
        except IndexError:
            raise self.DoesNotExist(
                "%s matching query does not exist." % self.__class__._meta.object_name
            )


class DeleteCaseProxy(Case):
    class Meta:
        proxy = True
        verbose_name = _("Cases to delete")
        verbose_name_plural = _("Cases to delete")


class CaseUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Case, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.permission.codename == "can_send_to_client":
            self.content_object.update_status()

    def delete(self, *args, **kwargs):
        """
        Note: this method is not invoked in usual circumstances (`remove_perm` call).
        """
        super().delete(*args, **kwargs)
        self.content_object.update_status()


class CaseGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Case, on_delete=models.CASCADE)


limit = {"content_type__app_label": "cases", "content_type__model": "case"}


class PermissionGroup(models.Model):
    name = models.CharField(max_length=25, verbose_name=_("Name"))
    permissions = models.ManyToManyField(
        to=Permission, verbose_name=_("Permissions"), limit_choices_to=limit
    )

    def __str__(self):
        return self.name

    @property
    def group_help_text(self):
        perm_name_list = [gettext(p.name) for p in self.permissions.all()]
        return f"\n{self.name}:\n" + "\n".join(
            [f"- {n}" for n in sorted(perm_name_list)]
        )


def notify_new_case(sender, instance, created, **kwargs):
    if created:
        User = get_user_model()
        users = User.objects.filter(notify_new_case=True).all()
        email = [x.email for x in users]
        TemplateMailManager.send(
            template_key=TemplateKey.CASE_NEW,
            recipient_list=email,
            context={"case": instance},
        )


post_save.connect(receiver=notify_new_case, sender=Case, dispatch_uid="new_case_notify")


def assign_perm_new_case(sender, instance, created, **kwargs):
    if created:
        instance.assign_perm()


post_save.connect(
    receiver=assign_perm_new_case, sender=Case, dispatch_uid="assign_perm_new_case"
)


def delete_files(sender, instance, **kwargs):
    delete_files_for_cases([instance])


pre_delete.connect(
    receiver=delete_files, sender=Case, dispatch_uid="delete_files_for_case"
)
