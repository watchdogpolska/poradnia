from datetime import datetime

from dateutil.rrule import rrule

from django.shortcuts import redirect


SECONDS_IN_A_DAY = 60 * 60 * 24
DATE_FORMAT = "%Y-%m-%d"

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
        ans = []
        params = None

        for i, temp in enumerate(self.qs[:-1]):
            a, b = self.qs[i], self.qs[i+1]
            date_range = self._date_range(a, b)
            params = self._get_params()

            ans.append(self._convert_date(a))
            ans.extend([self._construct(d) for d in date_range[1:-1]])
            if i == len(self.qs) - 2:  # check if last element
                ans.append(self._convert_date(b))
        return ans

    def _date_range(self, start, end):
        return list(rrule(
                            freq=self.freq,
                            dtstart=start[self.date_key],
                            until=end[self.date_key]))

    def _get_params(self):
        if hasattr(self, 'params'):
            return self.params
        else:
            keys = self.qs[0].keys()
            keys.remove(self.date_key)
            self.params = keys
            return self.params

    def _construct(self, date):
        obj = {p: 0 for p in self.params}
        obj[self.date_key] = date.strftime(self.date_format)
        return obj

    def _convert_date(self, obj):
        obj[self.date_key] = obj[self.date_key].strftime(self.date_format)
        return obj
