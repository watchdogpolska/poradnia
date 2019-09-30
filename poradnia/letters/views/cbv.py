import base64
import json
import uuid

from atom.ext.crispy_forms.views import FormSetMixin
from atom.ext.django_filters.filters import CrispyFilterMixin
from braces.views import (PrefetchRelatedMixin, SelectRelatedMixin,
                          SetHeadlineMixin, UserFormKwargsMixin)
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect, HttpResponseBadRequest, \
    JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import CreateView, UpdateView
import django_filters
from django_filters.views import FilterView

from poradnia.cases.models import Case
from poradnia.letters.settings import LETTER_RECEIVE_SECRET
from poradnia.users.utils import PermissionMixin

from .fbv import REGISTRATION_TEXT
from ..forms import AttachmentForm, LetterForm, NewCaseForm
from ..models import Attachment, Letter
from poradnia.cases.models import Case


class NewCaseCreateView(SetHeadlineMixin, FormSetMixin, UserFormKwargsMixin,
                        CreateView):
    model = Letter
    form_class = NewCaseForm
    headline = _('Create a new case')
    template_name = 'letters/form_new.html'
    inline_model = Attachment
    inline_form_cls = AttachmentForm

    def formset_valid(self, form, formset, *args, **kwargs):
        formset.save()
        messages.success(self.request,
                         _("Case about {object} created!").format(
                             object=self.object.name))
        self.object.client.notify(actor=self.object.created_by,
                                  verb='registered',
                                  target=self.object.case,
                                  from_email=self.object.case.get_email())
        if self.request.user.is_anonymous():
            messages.success(self.request, _(REGISTRATION_TEXT) % {
                'user': self.object.created_by})
        return HttpResponseRedirect(self.object.case.get_absolute_url())


class LetterUpdateView(SetHeadlineMixin, FormSetMixin, UserFormKwargsMixin,
                       UpdateView):
    model = Letter
    form_class = LetterForm
    headline = _('Edit')
    template_name = 'letters/form_edit.html'
    inline_model = Attachment
    inline_form_cls = AttachmentForm

    def get_context_data(self, **kwargs):
        context = super(LetterUpdateView, self).get_context_data(**kwargs)
        context['case'] = self.object.case
        return context

    def get_instance(self):
        return self.object

    def get_object(self):
        obj = super(LetterUpdateView, self).get_object()
        if obj.created_by_id == self.request.user.pk:
            obj.case.perm_check(self.request.user, 'can_change_own_record')
        else:
            obj.case.perm_check(self.request.user, 'can_change_all_record')
        return obj

    def get_formset_valid_message(self):
        return ("Letter %(object)s updated!") % {'object': self.object}

    def get_success_url(self):
        return self.object.case.get_absolute_url()

    def formset_valid(self, form, formset):
        resp = super(LetterUpdateView, self).formset_valid(form, formset)
        self.object.send_notification(actor=self.request.user, verb='updated')
        return resp


class StaffLetterFilter(CrispyFilterMixin, django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(
        label=_("Status"),
        # null_label=_("Any"),
        choices=[('', u'---------')] + Case.STATUS
    )

    def __init__(self, *args, **kwargs):
        super(StaffLetterFilter, self).__init__(*args, **kwargs)

    class Meta:
        model = Letter
        fields = ['status', ]


class UserLetterFilter(CrispyFilterMixin, django_filters.FilterSet):
    class Meta:
        model = Letter
        fields = []


class LetterListView(PermissionMixin, SelectRelatedMixin, PrefetchRelatedMixin,
                     FilterView):
    @property
    def filterset_class(self):
        return StaffLetterFilter if self.request.user.is_staff else UserLetterFilter

    model = Letter
    paginate_by = 20
    select_related = ['created_by', 'modified_by', 'case']
    prefetch_related = ['attachment_set', ]


class ReceiveEmailView(View):
    required_content_type = 'application/imap-to-webhook-v1+json'

    def post(self, request):
        if request.GET.get('secret') != LETTER_RECEIVE_SECRET:
            raise PermissionDenied
        if request.content_type != self.required_content_type:
            return HttpResponseBadRequest(
                'The request has an invalid format. '
                'The acceptable format is "{}"'.format(
                    self.required_content_type
                )
            )
        body = json.load(request)
        letter = self.get_letter(**body)

        Attachment.objects.bulk_create(
            self.get_attachment(attachment, letter)
            for attachment in body['files']
        )
        return JsonResponse({'status': 'OK', 'letter': letter.pk})

    def get_case(self, subject, addresses, actor):
        try:
            case = Case.objects.by_addresses(addresses).get()
        except Case.DoesNotExist:
            case = Case.objects.create(
                name=subject,
                created_by=actor,
                client=actor
            )
            actor.notify(
                actor=actor,
                verb='registered',
                target=case,
                from_email=case.get_email()
            )
        return case

    def get_letter_status(self, actor, case):
        if actor.is_staff and not actor.has_perm('cases.can_send_to_client',
                                                 case):
            return Letter.STATUS.staff
        else:
            return Letter.STATUS.done

    def get_letter(self, headers, eml, text, **kwargs):
        actor = get_user_model().objects.get_by_email_or_create(
            headers['from'][0]
        )
        case = self.get_case(headers['subject'], headers['to+'], actor)
        eml_file = self.get_eml_file(eml)

        return Letter.objects.create(
            name=headers['subject'],
            created_by=actor,
            case=case,
            status=self.get_letter_status(
                actor=actor,
                case=case
            ),
            text=text['content'],
            html='',
            signature=text['quote'],
            eml=eml_file
        )

    def get_attachment(self, attachment, letter):
        file_obj = ContentFile(content=base64.b64decode(attachment['content']),
                               name=attachment['filename'])
        return Attachment(letter=letter,
                          attachment=file_obj)

    def get_eml_file(self, eml):
        eml_extensions = "eml.gz" if eml['compressed'] else "eml"
        eml_filename = "{}.{}".format(uuid.uuid4().hex, eml_extensions)
        eml_content = base64.b64decode(eml['content'])
        return ContentFile(eml_content, eml_filename)
