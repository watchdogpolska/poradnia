from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^(?P<case_id>\d+)/add_permission$',
        views.PermissionCreate.as_view(), name="create"),

    url(r'^permission/(?P<pk>\d+)/delete$',
        views.PermissionDelete.as_view(), name="delete"),
    url(r'^permission/(?P<pk>\d+)/update$',
        views.PermissionUpdate.as_view(), name="update"),

)
