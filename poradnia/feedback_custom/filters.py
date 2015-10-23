from django.utils.translation import ugettext as _

from tasty_feedback.filters import FeedbackFilter
from users.filters import UserChoiceFilter


class AtomFeedbackFilter(FeedbackFilter):
    def __init__(self, *args, **kwargs):
        super(AtomFeedbackFilter, self).__init__(*args, **kwargs)
        self.filters['user'] = UserChoiceFilter(label=_("User"), name='user')
