from django.utils.translation import ugettext_lazy as _
from allauth.account.forms import LoginForm
from utilities.forms import SingleButtonMixin


class CustomLoginForm(SingleButtonMixin, LoginForm):
    action_text = _('Sign In')
