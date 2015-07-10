from crispy_forms.bootstrap import FormActions
from django.forms import Form
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.utils.translation import ugettext as _


class SaveButtonMixin(Form):
    def __init__(self, *args, **kwargs):
        super(SaveButtonMixin, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout.append(
            FormActions(
                Submit('save_changes', _('Update'), css_class="btn-primary"),
                Submit('cancel', _('Cancel')),
            )
        )
