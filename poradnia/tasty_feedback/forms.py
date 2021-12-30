from antispam.honeypot.forms import HoneypotField
from braces.forms import UserKwargModelFormMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import HiddenInput, ModelForm
from django.urls import reverse
from django.utils.translation import ugettext as _

from .models import Feedback


class FeedbackForm(UserKwargModelFormMixin, ModelForm):
    spam = HoneypotField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = getattr(self, "helper", FormHelper())
        self.helper.add_input(
            Submit("action", _("Submit feedback"), css_class="btn-primary")
        )
        self.fields["url"].widget = HiddenInput()
        self.helper.form_action = reverse("tasty_feedback:submit")

    def save(self, *args, **kwargs):
        if not self.user.is_anonymous:
            self.instance.user = self.user
        return super().save(*args, **kwargs)

    class Meta:
        model = Feedback
        fields = (
            "text",
            "url",
        )
