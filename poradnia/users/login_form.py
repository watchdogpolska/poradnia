from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
from allauth.account.forms import LoginForm
from utilities.forms import SingleButtonMixin


class CustomLoginForm(SingleButtonMixin, LoginForm):
    action_text = _l('Sign In')

    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].label = _('Login')
        self.helper.form_class = 'login-form'
