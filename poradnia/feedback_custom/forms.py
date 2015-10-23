from atom.forms import FormHorizontalMixin, SingleButtonMixin
from tasty_feedback.forms import FeedbackForm


class CustomFeedbackForm(FormHorizontalMixin, SingleButtonMixin, FeedbackForm):
    def __init__(self, *args, **kwargs):
        super(CustomFeedbackForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False
