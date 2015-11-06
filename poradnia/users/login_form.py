from allauth.account.forms import LoginForm
from crispy_forms.bootstrap import PrependedText
from crispy_forms.layout import Layout
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l

from atom.ext.cirspy_forms.forms import SingleButtonMixin


class CustomLoginForm(SingleButtonMixin, LoginForm):
    action_text = _l('Sign In')

    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].label = _('Login')
        self.helper.form_class = 'login-form'
        self.helper.layout = Layout(
                    PrependedText('login', '<i class="fa fa-user"></i>'),
                    PrependedText('password', '<i class="fa fa-key"></i>', type='password'),
            )
