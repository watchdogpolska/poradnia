from atom.ext.crispy_forms.forms import FormHorizontalMixin
from atom.ext.tinycontent.forms import GIODOMixin
from crispy_forms.bootstrap import PrependedText
from crispy_forms.layout import Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from turnstile.fields import TurnstileField


class SignupForm(
    FormHorizontalMixin,
    GIODOMixin,
    forms.ModelForm,
):

    turnstile = TurnstileField(label=_(" "), language="pl")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.label_class = "col-lg-3"
        self.helper.field_class = "col-lg-9"
        self.helper.layout = Layout(
            "first_name",
            "last_name",
            PrependedText("username", '<i class="fas fa-user"></i>'),
            PrependedText("email", "@"),
            PrependedText("password1", '<i class="fas fa-key"></i>', type="password"),
            PrependedText("password2", '<i class="fas fa-key"></i>', type="password"),
            "giodo",
            "turnstile",
        )
        self.helper.add_input(Submit("signup", _("Signup"), css_class="btn-primary"))

    class Meta:
        model = get_user_model()  # use this function for swapping user model
        fields = ["first_name", "last_name"]

    def save(self, user):
        user.save()

    def signup(self, request, user):
        pass
