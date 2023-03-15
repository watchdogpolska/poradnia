import json

import django_filters
from atom.ext.crispy_forms.views import FormSetMixin
from atom.ext.django_filters.filters import CrispyFilterMixin
from braces.views import (
    PrefetchRelatedMixin,
    SelectRelatedMixin,
    SetHeadlineMixin,
    UserFormKwargsMixin,
)
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.files.base import File
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, UpdateView
from django_filters.views import FilterView

from poradnia.cases.models import Case
from poradnia.letters.settings import LETTER_RECEIVE_SECRET
from poradnia.template_mail.utils import TemplateKey, TemplateMailManager
from poradnia.users.utils import PermissionMixin

from ..forms import AttachmentForm, LetterForm, NewCaseForm
from ..models import Attachment, Letter
from .fbv import REGISTRATION_TEXT


class NewCaseCreateView(
    SetHeadlineMixin, FormSetMixin, UserFormKwargsMixin, CreateView
):
    model = Letter
    form_class = NewCaseForm
    headline = _("Create a new case")
    template_name = "letters/form_new.html"
    inline_model = Attachment
    inline_form_cls = AttachmentForm

    def formset_valid(self, form, formset, *args, **kwargs):
        formset.save()
        messages.success(
            self.request,
            _("Case about {object} created!").format(object=self.object.name),
        )
        self.object.client.notify(
            actor=self.object.created_by,
            verb="registered",
            target=self.object.case,
            from_email=self.object.case.get_email(),
        )
        if self.request.user.is_anonymous:
            messages.success(
                self.request, _(REGISTRATION_TEXT) % {"user": self.object.created_by}
            )
        return HttpResponseRedirect(self.object.case.get_absolute_url())


class LetterUpdateView(SetHeadlineMixin, FormSetMixin, UserFormKwargsMixin, UpdateView):
    model = Letter
    form_class = LetterForm
    headline = _("Edit")
    template_name = "letters/form_edit.html"
    inline_model = Attachment
    inline_form_cls = AttachmentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["case"] = self.object.case
        return context

    def get_instance(self):
        return self.object

    def get_object(self):
        obj = super().get_object()
        if obj.created_by_id == self.request.user.pk:
            obj.case.perm_check(self.request.user, "can_change_own_record")
        else:
            obj.case.perm_check(self.request.user, "can_change_all_record")
        return obj

    def get_formset_valid_message(self):
        return ("Letter %(object)s updated!") % {"object": self.object}

    def get_success_url(self):
        return self.object.case.get_absolute_url()

    def formset_valid(self, form, formset):
        resp = super().formset_valid(form, formset)
        self.object.send_notification(actor=self.request.user, verb="updated")
        return resp


class StaffLetterFilter(CrispyFilterMixin, django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(
        label=_("Status"),
        # null_label=_("Any"),
        choices=[("", "---------")] + Case.STATUS,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Letter
        fields = ["status"]


class UserLetterFilter(CrispyFilterMixin, django_filters.FilterSet):
    class Meta:
        model = Letter
        fields = []


class LetterListView(
    PermissionMixin, SelectRelatedMixin, PrefetchRelatedMixin, FilterView
):
    @property
    def filterset_class(self):
        return StaffLetterFilter if self.request.user.is_staff else UserLetterFilter

    model = Letter
    paginate_by = 20
    select_related = ["created_by", "modified_by", "case"]
    prefetch_related = ["attachment_set"]


class ReceiveEmailView(View):
    required_content_type = "multipart/form-data"

    def is_allowed_recipient(self, manifest):
        domain = Site.objects.get_current().domain
        cond = [
            (addr in x or domain in x) and addr != '' and domain != ''
            for x in manifest["headers"]["to"]
            for addr in settings.LETTER_RECEIVE_WHITELISTED_ADDRESS
        ]
        return any(cond)

    def is_autoreply(self, manifest):
        return manifest["headers"].get("auto_reply_type", False)

    def create_user(self, manifest):
        return get_user_model().objects.get_by_email_or_create(
            manifest["headers"]["from"][0]
        )

    def create_case(self, manifest, actor):
        return self.get_case(
            subject=manifest["headers"]["subject"],
            addresses=manifest["headers"]["to+"],
            actor=actor,
        )

    def refuse_letter(self, manifest):
        context = {
            "to": manifest["headers"]["to"],
            "subject": manifest["headers"]["subject"],
        }
        TemplateMailManager.send(
            TemplateKey.LETTER_REFUSED,
            recipient_list=manifest["headers"]["from"],
            context=context,
        )

    def create_letter(self, request, actor, case, manifest):
        letter = Letter.objects.create(
            name=manifest["headers"]["subject"],
            created_by=actor,
            created_by_is_staff=actor.is_staff,
            case=case,
            genre=Letter.GENRE.mail,
            status=self.get_letter_status(actor=actor, case=case),
            text=manifest["text"]["content"],
            html="",
            signature=manifest["text"]["quote"],
            eml=File(self.request.FILES["eml"]),
        )
        for attachment in request.FILES.getlist("attachment"):
            Attachment.objects.create(letter=letter, attachment=File(attachment))
        return letter

    def post(self, request):
        if request.GET.get("secret") != LETTER_RECEIVE_SECRET:
            raise PermissionDenied
        if request.content_type != self.required_content_type:
            return HttpResponseBadRequest(
                "The request has an invalid format. "
                'The acceptable format is "{}"'.format(self.required_content_type)
            )
        if "manifest" not in request.FILES:
            return HttpResponseBadRequest(
                "The request has an invalid format. Missing 'manifest' filed."
            )
        if "eml" not in request.FILES:
            return HttpResponseBadRequest(
                "The request has an invalid format. Missing 'eml' filed."
            )
        manifest = json.load(request.FILES["manifest"])

        REFUSE_MESSAGE = (
            "There is no e-mail address for the target system in the recipient field. "
        )
        if not self.is_allowed_recipient(manifest):
            if not self.is_autoreply(manifest):
                self.refuse_letter(manifest)
                return HttpResponseBadRequest(
                    REFUSE_MESSAGE + "Notification have been send."
                )
            return HttpResponseBadRequest(
                REFUSE_MESSAGE + "Notification have been skipped."
            )
        actor = self.create_user(manifest)
        case = self.create_case(manifest, actor)
        letter = self.create_letter(request, actor, case, manifest)
        if case.status == Case.STATUS.closed and letter.status == Letter.STATUS.done:
            case.update_status(reopen=True, save=False)
        case.handled = actor.is_staff is True and letter.status == Letter.STATUS.done
        case.update_counters()
        case.save()
        letter.send_notification(actor=actor, verb="created")
        return JsonResponse({"status": "OK", "letter": letter.pk})

    def get_case(self, subject, addresses, actor):
        try:
            case = Case.objects.by_addresses(addresses).get()
        except Case.DoesNotExist:
            case = Case.objects.create(name=subject, created_by=actor, client=actor)
            actor.notify(
                actor=actor, verb="registered", target=case, from_email=case.get_email()
            )
        return case

    def get_letter_status(self, actor, case):
        if actor.is_staff and not actor.has_perm("cases.can_send_to_client", case):
            return Letter.STATUS.staff
        else:
            return Letter.STATUS.done
