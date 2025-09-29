from allauth.account.forms import LoginForm
from crispy_forms.bootstrap import PrependedText
from crispy_forms.layout import Layout
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l

from poradnia.utils.crispy_forms import SingleButtonMixin


class CustomLoginForm(SingleButtonMixin, LoginForm):
    action_text = _l("Sign In")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["login"].label = _("Login")
        self.helper.form_class = "login-form"
        self.helper.layout = Layout(
            PrependedText("login", mark_safe('<i class="fas fa-user"></i>')),
            PrependedText(
                "password", mark_safe('<i class="fas fa-key"></i>'), type="password"
            ),
        )
