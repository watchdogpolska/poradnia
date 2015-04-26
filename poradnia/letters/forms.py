from django.forms import ModelForm
from django import forms
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from .helpers import FormsetHelper
from cases.models import Case
from functools import partial
from .models import Letter, Attachment


class PartialMixin(object):
    @classmethod
    def partial(cls, *args, **kwargs):
        return partial(cls, *args, **kwargs)


class NewCaseForm(ModelForm, PartialMixin):
    client = forms.ModelChoiceField(queryset=get_user_model().objects.all(), required=False)
    email = forms.EmailField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.helper = FormsetHelper()
        super(NewCaseForm, self).__init__(*args, **kwargs)
        if not self.user.has_perm('cases.can_select_client'):
            del self.fields['client']
            del self.fields['email']
        else:
            self.fields['client'].initial = self.user

    def clean(self):

        if self.user.has_perm('cases.can_select_client') and \
                not (self.cleaned_data.get('email') or self.cleaned_data.get('client')):
            raise ValidationError("Have to enter 'email' or 'client'")

        return self.cleaned_data

    def get_client(self):
        # If client selected - use it
        if not self.user.has_perm('cases.can_select_client'):
            return self.user
        elif self.cleaned_data['client']:
            return self.cleaned_data['client']
        elif self.cleaned_data['email']:
            return get_user_model().objects.get_by_email_or_create(self.cleaned_data['email'])
        return self.user

    def get_case(self, client):
        # Create new_case
        case = Case(name=self.cleaned_data['name'], created_by=self.user, client=client)
        case.save()
        return case

    def save(self, commit=False, *args, **kwargs):
        obj = super(NewCaseForm, self).save(commit=False, *args, **kwargs)
        obj.status = obj.STATUS.done
        obj.created_by = self.user
        obj.client = self.get_client()
        obj.case = self.get_case(client=obj.client)
        if kwargs.get('commit', False):
            obj.save()
        return obj

    class Meta:
        fields = ['name', 'text']
        model = Letter


class AddLetterForm(ModelForm, PartialMixin):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.case = kwargs.pop('case')
        self.helper = FormsetHelper()
        self.helper.form_action = reverse('letters:add', kwargs={'case_pk': self.case.pk})
        super(AddLetterForm, self).__init__(*args, **kwargs)
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


class SendLetterForm(ModelForm, PartialMixin):
    comment = forms.CharField(widget=forms.widgets.Textarea)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        ins = kwargs['instance']
        self.helper = FormsetHelper()
        self.helper.form_action = ins.get_send_url()
        super(SendLetterForm, self).__init__(*args, **kwargs)

    def save(self, commit=True, *args, **kwargs):
        obj = super(SendLetterForm, self).save(commit=False, *args, **kwargs)
        obj.modified_by = self.user
        obj.status = obj.STATUS.done
        obj.save()
        obj.send_notification(self.user, 'send to client')
        msg = Letter(case=obj.case, created_by=self.user, text=self.cleaned_data['comment'], status=obj.STATUS.staff)
        msg.save()
        msg.send_notification(self.user, 'drop a note')
        return obj

    class Meta:
        model = Letter
        fields = []


class AttachmentForm(ModelForm):
    class Meta:
        fields = ['attachment']
        model = Attachment


class LetterForm(ModelForm, PartialMixin):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.helper = FormsetHelper()
        self.helper.form_action = kwargs['instance'].get_edit_url()
        self.helper.form_method = 'post'
        super(LetterForm, self).__init__(*args, **kwargs)
        if self.user.is_authenticated() and not self.user.has_perm('cases.can_send_to_client'):
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
