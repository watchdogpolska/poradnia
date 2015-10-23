# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('notifications_custom.views',
    url(r'^$', views.NotificationListView.as_view(), name='all'),
)

urlpatterns += patterns('notifications.views',
    url(r'^unread/$', 'unread', name='unread'),
    url(r'^mark-all-as-read/$', 'mark_all_as_read', name='mark_all_as_read'),
    url(r'^mark-as-read/(?P<slug>\d+)/$', 'mark_as_read', name='mark_as_read'),
    url(r'^mark-as-unread/(?P<slug>\d+)/$', 'mark_as_unread', name='mark_as_unread'),
)
