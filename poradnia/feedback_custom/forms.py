from poradnia.tasty_feedback.forms import FeedbackForm
from poradnia.utils.crispy_forms import FormHorizontalMixin, SingleButtonMixin


class CustomFeedbackForm(FormHorizontalMixin, SingleButtonMixin, FeedbackForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_tag = False
