from datetime import datetime

from dateutil.rrule import rrule

from django.shortcuts import redirect


SECONDS_IN_A_DAY = 60 * 60 * 24

def raise_unless_unauthenticated(view, request):
    # Hack from SO due to https://github.com/brack3t/django-braces/issues/181 bug
    if not request.user.is_authenticated():
        return redirect('/konta/login/?next=%s' % request.path)
    return None

def fill_gaps(qs, freq, date_key, constructor):
    ans = []
    for i, el in enumerate(qs[:-1]):
        a, b = qs[i], qs[i+1]
        date_range = list(rrule(freq=freq, dtstart=date_key(a), until=date_key(b)))

        ans.append(a)
        ans.extend([constructor(d) for d in date_range[1:-1]])
        if i == len(qs) - 2:  # check if last element
            ans.append(b)
    return ans
