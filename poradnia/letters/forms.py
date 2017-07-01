import autocomplete_light.shortcuts as autocomplete_light
from crispy_forms.layout import BaseInput, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from atom.ext.crispy_forms.forms import HelperMixin, SingleButtonMixin
from atom.ext.tinycontent.forms import GIODOMixin
from atom.forms import PartialMixin
from poradnia.cases.models import Case
from .models import Attachment, Letter

CLIEN_FIELD_TEXT = _("Leave empty to use email field and create a new one user.")

EMAIL_TEXT = _("""The user account will be created automatically, so you have
access to the archive and data about persons responsible for the case.""")

CASE_NAME_TEXT = _(""""Short description of the case for organizational purposes.
The institution name and two words will suffice.""")


class SimpleSubmit(BaseInput):
    input_type = 'submit'
    field_classes = 'btn'


class UserEmailField(forms.EmailField):
    def validate(self, value):
        "Check if value consists only of unique user emails."
        super(UserEmailField, self).validate(value)
        if get_user_model().objects.filter(email=value).exists():
            raise ValidationError(
                _('E-mail %(email)s are already used. Please log in.'),
                code='invalid',
                params={'email': value},
            )


class NewCaseForm(SingleButtonMixin, PartialMixin, GIODOMixin, autocomplete_light.ModelForm):
    attachment_cls = Attachment
    attachment_rel_field = 'letter'
    attachment_file_field = 'attachment'
    action_text = _("Report case")

    client = forms.ModelChoiceField(queryset=get_user_model().objects.none(),
                                    label=_("Client"),
                                    required=False,
                                    help_text=CLIEN_FIELD_TEXT,
                                    widget=autocomplete_light.ChoiceWidget('UserAutocomplete'))
    email = forms.EmailField(required=False,
                             label=_("User e-mail"))
    email_registration = UserEmailField(required=True,
                                        help_text=EMAIL_TEXT,
                                        label=_("E-mail"))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(NewCaseForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False
        self.helper.form_method = 'post'
        self.fields['name'].help_text = CASE_NAME_TEXT

        if self._is_super_staff():
            self.fields['client'].initial = self.user
            self.fields['client'].queryset = (get_user_model().objects.
                                              for_user(self.user).all())
        else:
            del self.fields['client']
            del self.fields['email']

        if not self.user.is_anonymous():  # is registered
            del self.fields['email_registration']

        if not (self.user.is_anonymous() or self._is_super_staff()):
            del self.fields['giodo']
        elif self._is_super_staff():
            self.fields['giodo'].required = False

    def _is_super_staff(self):
        return self.user.has_perm('cases.can_select_client')

    def clean(self):
        if self.user.has_perm('cases.can_select_client') and \
            not (self.cleaned_data.get('email') or self.cleaned_data.get('client')):
            raise ValidationError(_("Have to enter user email or select a client"))
        return super(NewCaseForm, self).clean()

    def get_user(self):
        if self.user.is_anonymous():
            return get_user_model().objects.get_by_email_or_create(
                self.cleaned_data['email_registration'])
        return self.user

    def get_client(self, user):
        if self.user.is_anonymous() and self.cleaned_data['email_registration']:
            return user
        if not self.user.has_perm('cases.can_select_client'):
            return self.user
        elif self.cleaned_data['client']:
            return self.cleaned_data['client']
        elif self.cleaned_data['email']:
            return get_user_model().objects.get_by_email_or_create(self.cleaned_data['email'])
        return self.user

    def get_case(self, client, user):
        case = Case(name=self.cleaned_data['name'], created_by=user, client=client)
        case.save()
        return case

    def save(self, commit=True, *args, **kwargs):
        user = self.get_user()
        obj = super(NewCaseForm, self).save(commit=False, *args, **kwargs)
        obj.status = obj.STATUS.done
        obj.created_by = user
        obj.client = self.get_client(user)
        if not obj.case_id:
            obj.case = self.get_case(client=obj.client, user=user)
        if commit:
            obj.save()
        return obj

    class Meta:
        fields = ['name', 'text']
        model = Letter


class AddLetterForm(HelperMixin, PartialMixin, ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.case = kwargs.pop('case')
        self.user_can_send = self.user.has_perm('cases.can_send_to_client', self.case)
        super(AddLetterForm, self).__init__(*args, **kwargs)
        self.helper.form_action = reverse('letters:add', kwargs={'case_pk': self.case.pk})
        self.helper.form_tag = False
        self._add_buttons()
        self.fields['name'].initial = "Odp: %s" % (self.case)

    def _add_buttons(self):
        if self.user_can_send:
            self.helper.add_input(Submit(name='send',
                                         value=_("Reply to all"),
                                         css_class="btn-primary"))
            self.helper.add_input(Submit(name='project',
                                         value=_("Save to review"),
                                         css_class="btn-primary"))
            self.helper.add_input(SimpleSubmit(name='send_staff',
                                               input_type='submit',
                                               value=_("Reply to staff"),
                                               css_class="btn-default"))
        else:
            if self.user.is_staff:
                self.helper.add_input(Submit(name='send',
                                             value=_("Reply to staff"),
                                             css_class="btn-primary"))
                self.helper.add_input(Submit(name='project',
                                             value=_("Save to review"),
                                             css_class="btn-primary"))
            else:
                self.helper.add_input(Submit(name='send',
                                             value=_("Reply"),
                                             css_class="btn-primary"))

    def get_status(self):
        if not self.user.is_staff:
            return Letter.STATUS.done
        if not self.user_can_send:
            return Letter.STATUS.staff
        if 'send_staff' in self.data or 'project' in self.data:
            return Letter.STATUS.staff
        return Letter.STATUS.done

    def save(self, commit=True, *args, **kwargs):
        obj = super(AddLetterForm, self).save(commit=False, *args, **kwargs)
        obj.status = self.get_status()
        obj.created_by = self.user
        obj.case = self.case
        if self.user.is_staff:
            if 'project' in self.data:
                self.case.has_project = True
            elif obj.status == Letter.STATUS.done:
                self.case.has_project = False
                self.case.handled = True
        else:
            self.case.handled = False
            if self.case.status == Case.STATUS.closed:
                self.case.status_update(reopen=True, save=False)
        self.case.save()
        if commit:
            obj.save()
        return obj

    class Meta:
        fields = ['name', 'text']
        model = Letter


class SendLetterForm(SingleButtonMixin, PartialMixin, ModelForm):
    comment = forms.CharField(widget=forms.widgets.Textarea,
                              label=_("Comment for staff"),
                              required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        ins = kwargs['instance']
        super(SendLetterForm, self).__init__(*args, **kwargs)
        self.helper.form_action = ins.get_send_url()

    def save(self, commit=True, *args, **kwargs):
        obj = super(SendLetterForm, self).save(commit=False, *args, **kwargs)
        obj.modified_by = self.user
        obj.status = obj.STATUS.done
        obj.save()

        obj.case.handled = True
        obj.case.has_project = False
        obj.case.save()

        obj.send_notification(actor=self.user, verb='send_to_client')
        if self.cleaned_data['comment']:
            msg = Letter(case=obj.case,
                         created_by=self.user,
                         text=self.cleaned_data['comment'],
                         status=obj.STATUS.staff)
            msg.save()
            msg.send_notification(actor=self.user, verb='drop_a_note')
        return obj

    class Meta:
        model = Letter
        fields = []


class AttachmentForm(ModelForm):
    class Meta:
        fields = ['attachment']
        model = Attachment


class LetterForm(SingleButtonMixin, PartialMixin, ModelForm):  # eg. edit form
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(LetterForm, self).__init__(*args, **kwargs)
        self.helper.form_action = kwargs['instance'].get_edit_url()
        self.helper.form_method = 'post'

    def save(self, commit=True, *args, **kwargs):
        obj = super(LetterForm, self).save(commit=False, *args, **kwargs)
        obj.modified_by = self.user
        obj.save()
        return obj

    class Meta:
        fields = ['name', 'text']
        model = Letter
