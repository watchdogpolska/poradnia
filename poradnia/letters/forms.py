from django.forms import ModelForm
from django import forms
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
import autocomplete_light
from cases.models import Case
from utilities.forms import FileMixin, PartialMixin, SingleButtonMixin
from .helpers import FormsetHelper
from .models import Letter, Attachment

EMAIL_HELP_TEXT = _l("The user account will be created automatically," +
    "so you have access to the archive and data about persons responsible for the case.")


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


class NewCaseForm(autocomplete_light.ModelForm, SingleButtonMixin, FileMixin, PartialMixin):
    form_helper_cls = FormsetHelper
    attachment_cls = Attachment
    action_text = _l("Report case")

    client = forms.ModelChoiceField(queryset=get_user_model().objects.all(), label=_("Client"),
        required=False, help_text=_("Leave empty to use email field and create a new one user."),
        widget=autocomplete_light.ChoiceWidget('UserAutocomplete'))
    email = forms.EmailField(required=False, label=_("User e-mail"))
    email_registration = UserEmailField(required=True, help_text=_(EMAIL_HELP_TEXT),
        label=_("E-mail"))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(NewCaseForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False
        self.helper.form_method = 'post'
        self.fields['name'].help_text = _("Short description of the case for organizational " +
            "purposes. The institution name and two words will suffice.")
        if not self.user.has_perm('cases.can_select_client'):
            del self.fields['client']
            del self.fields['email']
        else:
            self.fields['client'].initial = self.user

        if not self.user.is_anonymous():
            del self.fields['email_registration']

    def clean(self):
        if self.user.has_perm('cases.can_select_client') and \
                not (self.cleaned_data.get('email') or self.cleaned_data.get('client')):
            raise ValidationError(_("Have to enter user email or select a client"))
        return self.cleaned_data

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
        obj.case = self.get_case(client=obj.client, user=user)
        if commit:
            obj.save()
        return obj

    class Meta:
        fields = ['name', 'text']
        model = Letter


class AddLetterForm(ModelForm, SingleButtonMixin, PartialMixin):
    form_helper_cls = FormsetHelper

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.case = kwargs.pop('case')
        super(AddLetterForm, self).__init__(*args, **kwargs)
        self.helper.form_action = reverse('letters:add', kwargs={'case_pk': self.case.pk})
        import ipdb; ipdb.set_trace()
        self.fields['name'].initial = "Odp: %s" % (self.case)
        if not self.user.has_perm('cases.can_send_to_client'):
            del self.fields['status']

    def save(self, commit=True, *args, **kwargs):
        obj = super(AddLetterForm, self).save(commit=False, *args, **kwargs)
        if not self.user.has_perm('cases.can_send_to_client'):  # if user or student
            obj.status = obj.STATUS.staff if self.user.is_staff else obj.STATUS.done
        obj.created_by = self.user
        obj.case = self.case
        if commit:
            obj.save()
        obj.send_notification(self.user, 'created')
        return obj

    class Meta:
        fields = ['name', 'text', 'status']
        model = Letter


class SendLetterForm(ModelForm, SingleButtonMixin, PartialMixin):
    comment = forms.CharField(widget=forms.widgets.Textarea, label=_("Comment for staff"))

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
        obj.send_notification(self.user, 'send_to_client')
        msg = Letter(case=obj.case, created_by=self.user, text=self.cleaned_data['comment'],
            status=obj.STATUS.staff)
        msg.save()
        msg.send_notification(self.user, 'drop_a_note', staff=True)
        return obj

    class Meta:
        model = Letter
        fields = []


class AttachmentForm(ModelForm):
    class Meta:
        fields = ['attachment']
        model = Attachment


class LetterForm(ModelForm, SingleButtonMixin, PartialMixin):  # eg. edit form
    form_helper_cls = FormsetHelper

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(LetterForm, self).__init__(*args, **kwargs)
        self.helper.form_action = kwargs['instance'].get_edit_url()
        self.helper.form_method = 'post'
        if not self.user.has_perm('cases.can_send_to_client'):
            del self.fields['status']

    def save(self, commit=True, *args, **kwargs):
        obj = super(LetterForm, self).save(commit=False, *args, **kwargs)
        obj.modified_by = self.user
        obj.save()
        obj.send_notification(self.user, 'updated')
        return obj

    class Meta:
        fields = ['name', 'text', 'status']
        model = Letter
