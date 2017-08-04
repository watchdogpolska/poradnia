from datetime import datetime

from dateutil.rrule import MONTHLY, WEEKLY, rrule
from django.shortcuts import redirect

SECONDS_IN_A_DAY = 60 * 60 * 24
DATE_FORMAT_MONTHLY = "%Y-%m"
DATE_FORMAT_WEEKLY = "%Y-%W"


def raise_unless_unauthenticated(view, request):
    # Hack from SO due to https://github.com/brack3t/django-braces/issues/181 bug
    if not request.user.is_authenticated():
        return redirect('/konta/login/?next=%s' % request.path)
    return None


class GapFiller(object):
    def __init__(self, qs, freq, date_key, date_format):
        self.qs = list(qs)
        self.freq = freq
        self.date_key = date_key
        self.date_format = date_format

    def fill_gaps(self):
        if len(self.qs) == 1:
            # return [self._convert_date(self.qs[0])]
            return self.qs

        ans = []
        params = None

        for i, temp in enumerate(self.qs[:-1]):
            a, b = self.qs[i], self.qs[i + 1]
            date_range = self._date_range(a, b)
            params = self._get_params()

            ans.append(a)
            ans.extend([self._construct(d) for d in date_range[1:-1]])
            if i == len(self.qs) - 2:  # check if last element
                ans.append(b)
        return ans

    def _date_range(self, start, end):
        if self.freq == MONTHLY:
            date_format = DATE_FORMAT_MONTHLY
            start = start[self.date_key]
            end = end[self.date_key]
            return list(rrule(
                freq=self.freq,
                dtstart=datetime.strptime(start, date_format),
                until=datetime.strptime(end, date_format)))
        if self.freq == WEEKLY:
            date_format = DATE_FORMAT_WEEKLY + "-%w"  # append weekday to parse date by week number
            start = start[self.date_key] + "-1"
            end = end[self.date_key] + "-1"
            return list(rrule(
                freq=self.freq,
                dtstart=datetime.strptime(start, date_format),
                until=datetime.strptime(end, date_format)))

    def _get_params(self):
        if hasattr(self, 'params'):
            return self.params
        else:
            keys = list(self.qs[0].keys())
            keys.remove(self.date_key)
            self.params = keys
            return self.params

    def _construct(self, date):
        obj = {p: 0 for p in self.params}
        obj[self.date_key] = date.strftime(self.date_format)
        return obj


def filter_today(qs, field):
    today = datetime.today()
    return qs.filter(**{'{}__date__gte'.format(field): today})


def filter_month(qs, field):
    start = datetime.today().replace(day=1)
    return qs.filter(**{'{}__date__gte'.format(field): start})
