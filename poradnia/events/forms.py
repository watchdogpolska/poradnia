from atom.ext.crispy_forms.forms import FormHorizontalMixin, SingleButtonMixin
from atom.forms import AuthorMixin
from django import forms
from django.urls import reverse

from poradnia.letters.forms import PartialMixin

from .models import Event


class EventForm(
    PartialMixin, AuthorMixin, FormHorizontalMixin, SingleButtonMixin, forms.ModelForm
):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.case = kwargs.pop("case")
        super().__init__(*args, **kwargs)
        self.helper.form_action = reverse(
            "events:add", kwargs={"case_pk": self.case.pk}
        )
        if kwargs.get("instance", False):
            self.helper.form_action = kwargs["instance"].get_edit_url()

    def save(self, commit=True, *args, **kwargs):
        obj = super().save(commit=False, *args, **kwargs)
        created = obj.pk is None
        obj.case = self.case
        obj.save()
        verb = "created" if created else "updated"
        obj.send_notification(
            actor=self.user,
            user_qs=self.case.get_users_with_perms().filter(is_staff=True),
            verb=verb,
        )
        return obj

    class Meta:
        # Set this form to use the User model.
        model = Event
        fields = ("deadline", "time", "text")
        widgets = {"time": forms.DateTimeInput(attrs={"autocomplete": "off"})}
