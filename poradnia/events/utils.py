from calendar import LocaleHTMLCalendar
from datetime import date
from itertools import groupby
from django.utils.html import conditional_escape as esc


class AbstractCalendar(LocaleHTMLCalendar):
    field = 'time'

    def __init__(self, events, *args, **kwargs):
        super(AbstractCalendar, self).__init__(*args, **kwargs)
        self.events = self.group_by_day(events)

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            if date.today() == date(self.year, self.month, day):
                cssclass += ' today'
            if day in self.events:
                cssclass += ' filled'
                body = ['<ul>']
                for event in self.events[day]:
                    body.append(self.get_row_content(event))
                body.append('</ul>')
                html = '<span class="day">%d</span> %s' % (day, ''.join(body))
                return self.day_cell(cssclass, html)
            return self.day_cell(cssclass, day)
        return self.day_cell('noday', '&nbsp;')

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super(AbstractCalendar, self).formatmonth(year, month)

    def group_by_day(self, events):
        return {day: list(items) for day, items in groupby(events, lambda x: getattr(x, self.field).day)}

    def day_cell(self, cssclass, body):
        return '<td class="%s">%s</td>' % (cssclass, body)

    def get_field(self):
        return self.field

    def get_row_content(self, event):
        raise NotImplementedError("Method 'get_row_content' should be overwriten.")


class EventCalendar(AbstractCalendar):
    field = 'time'

    def get_row_content(self, event):
        text = ''
        text += '<li'
        if event.deadline:
            text += ' class="deadline"'
        text += '>'
        text += '<a href="{0}" title="{1}">'.format(event.get_absolute_url(), event.text)
        text += esc(event.case)
        text += '</a></li>'
        return text
