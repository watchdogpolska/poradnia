from calendar import HTMLCalendar
from datetime import date
from itertools import groupby

from django.utils.html import conditional_escape as esc
from django.utils.translation import ugettext_lazy as _

day_name = [
    _("Monday"),
    _("Tuesday"),
    _("Wednesday"),
    _("Thursday"),
    _("Friday"),
    _("Saturday"),
    _("Sunday"),
]
day_abbr = [_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun")]

month_name = [
    _("January"),
    _("February"),
    _("March"),
    _("April"),
    _("May"),
    _("June"),
    _("July"),
    _("August"),
    _("September"),
    _("October"),
    _("November"),
    _("December"),
]

month_abbr = [
    _("Jan"),
    _("Feb"),
    _("Mar"),
    _("Apr"),
    _("May"),
    _("Jun"),
    _("Jul"),
    _("Aug"),
    _("Sep"),
    _("Oct"),
    _("Nov"),
    _("Dec"),
]

EVENT_CONTENT = '<li{class_attr}><a href="{link}" title="{title}">{content}</a></li>'


class AbstractCalendar(HTMLCalendar):
    field = "time"

    def __init__(self, events, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = self.group_by_day(events)

    def formatmonthname(self, theyear, themonth, withyear=True):
        """
        Return a month name as a table row.
        """
        if withyear:
            s = "{} {}".format(month_name[themonth - 1], theyear)
        else:
            s = "%s" % month_name[themonth]
        return '<tr><th colspan="7" class="month">%s</th></tr>' % s

    def formatweekday(self, day):
        """
        Return a weekday name as a table header.
        """
        return '<th class="{}">{}</th>'.format(self.cssclasses[day], day_abbr[day])

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            if date.today() == date(self.year, self.month, day):
                cssclass += " today"
            if day in self.events:
                cssclass += " filled"
                body = ["<ul>"]
                for event in self.events[day]:
                    body.append(self.get_row_content(event))
                body.append("</ul>")
                html = '<span class="day">%d</span> %s' % (day, "".join(body))
                return self.day_cell(cssclass, html)
            return self.day_cell(cssclass, '<span class="day">%d</span>' % day)
        return self.day_cell("noday", "&nbsp;")

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super().formatmonth(year, month)

    def group_by_day(self, events):
        return {day: list(items) for day, items in groupby(events, self.get_field)}

    def day_cell(self, cssclass, body):
        return '<td class="{}">{}</td>'.format(cssclass, body)

    def get_field_name(self):
        return self.field

    def get_field(self, obj):
        return getattr(obj, self.get_field_name()).day

    def get_row_content(self, event):
        raise NotImplementedError("Method 'get_row_content' should be overwritten.")


class EventCalendar(AbstractCalendar):
    field = "time"

    def get_row_content(self, event):
        text = EVENT_CONTENT.format(
            class_attr=' class="deadline"' if event.deadline else "",
            link=event.get_absolute_url(),
            title=event.text,
            content=esc(event.case),
        )
        return text
