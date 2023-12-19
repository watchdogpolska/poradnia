from django.urls import path

from . import views

urlpatterns = [
    path("sprawa-<int:case_pk>/", views.EventCreateView.as_view(), name="add"),
    path("wydarzenie-<int:pk>", views.EventUpdateView.as_view(), name="edit"),
    path(
        "<int:year>-<int:month>",
        views.CalendarEventView.as_view(month_format="%m"),
        name="calendar",
    ),
    path("", views.CalendarListView.as_view(), name="calendar"),
    path("ical/", views.ICalendarView.as_view(), name="calendar_ical"),
    path("table/", views.EventTableView.as_view(), name="table"),
    path(
        "events_table_ajax_data/",
        views.EventAjaxDatatableView.as_view(),
        name="events_table_ajax_data",
    ),
]

app_name = "poradnia.events"
