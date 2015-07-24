from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.CaseListView.as_view(), name="list"),
    url(r'^case-(?P<pk>\d+)/edit$', views.CaseUpdateView.as_view(), name="edit"),
    url(r'^case-(?P<pk>\d+)/permission$', views.UserPermissionCreateView.as_view(),
        name="permission_add"),
    url(r'^case-(?P<pk>\d+)/permission/(?P<user_pk>\d+)$', views.UserPermissionUpdateView.as_view(),
        name="permission_update"),
    url(r'^case-(?P<pk>\d+)/permission/grant$', views.CaseGroupPermissionView.as_view(),
        name="permission_grant"),
    url(r'^case-(?P<pk>\d+)/$', views.CaseDetailView.as_view(), name="detail"),
)
