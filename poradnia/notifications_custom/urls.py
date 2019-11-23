from django.urls import path

import notifications

from . import views

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="all"),
    path("unread", notifications.views.unread, name="unread"),
    path(
        "mark-all-as-read",
        notifications.views.mark_all_as_read,
        name="mark_all_as_read",
    ),
    path(
        "mark-as-read/<int:slug>", notifications.views.mark_as_read, name="mark_as_read"
    ),
    path(
        "mark-as-unread/<int:slug>",
        notifications.views.mark_as_unread,
        name="mark_as_unread",
    ),
]
