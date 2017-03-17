from django.utils.translation import ugettext as _

from poradnia.tasty_feedback.filters import FeedbackFilter
from poradnia.users.filters import UserChoiceFilter


class AtomFeedbackFilter(FeedbackFilter):
    def __init__(self, *args, **kwargs):
        super(AtomFeedbackFilter, self).__init__(*args, **kwargs)
        self.filters['user'] = UserChoiceFilter(label=_("User"), name='user')
