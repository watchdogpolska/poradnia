from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import HiddenInput, ModelForm
from django.urls import reverse
from django.utils.translation import gettext as _

from poradnia.utils.view_mixins import UserKwargModelFormMixin

from .models import Feedback


class FeedbackForm(UserKwargModelFormMixin, ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = getattr(self, "helper", FormHelper())
        self.helper.add_input(
            # Not "action": SingleButtonMixin's forms (poradnia/utils/
            # crispy_forms_helpers.py) also use that name for their submit
            # button, and crispy-forms generates predictable
            # submit-id-{name} ids - any page showing both this widget and
            # a SingleButtonMixin form ends up with two elements sharing
            # id="submit-id-action" (confirmed live on case_detail.html's
            # court-case form). See audit/findings.csv F016.
            Submit("feedback_action", _("Submit feedback"), css_class="btn-primary")
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
