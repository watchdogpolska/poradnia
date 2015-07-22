from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^case-(?P<case_pk>\d+)$', views.EventCreateView.as_view(), name="add"),
    url(r'^event-(?P<pk>\d+)/edit$', views.EventUpdateView.as_view(), name="edit"),
    url(r'^event-(?P<pk>\d+)/dismiss$', views.dismiss, name="dismiss"),
    url(r'^(?P<year>\d+)-(?P<month>\d+)$', views.CalendarEventView.as_view(month_format='%m'), name="calendar"),
    url(r'^$', views.CalendarListView.as_view(), name="calendar"),
    url(r'^ical/$', views.ICalendarView.as_view(), name="calendar_ical"),

)
