from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.CaseListView.as_view(), name="list"),
    url(r'^sprawa-(?P<pk>\d+)/edytuj/$', views.CaseUpdateView.as_view(), name="edit"),
    url(r'^sprawa-(?P<pk>\d+)/zamknij/$', views.CaseCloseView.as_view(), name="close"),
    url(r'^sprawa-(?P<pk>\d+)/uprawnienia/$', views.UserPermissionCreateView.as_view(),
        name="permission_add"),
    url(r'^sprawa-(?P<pk>\d+)/uprawnienia-(?P<username>[\w.@+-]+)/$',
        views.UserPermissionUpdateView.as_view(),
        name="permission_update"),
    url(r'^sprawa-(?P<pk>\d+)/uprawnienia-(?P<username>[\w.@+-]+)/~remove$',
        views.UserPermissionRemoveView.as_view(),
        name="permission_remove"),
    url(r'^sprawa-(?P<pk>\d+)/uprawnienia/przyznaj/$',
        views.CaseGroupPermissionView.as_view(),
        name="permission_grant"),
    url(r'^sprawa-(?P<pk>\d+)/$', views.CaseDetailView.as_view(),
        name="detail"),
    url(r'^~autocomplete$', views.CaseAutocomplete.as_view(),
        name="autocomplete"),

]
