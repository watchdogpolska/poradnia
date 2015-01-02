from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.CaseList.as_view(), name="list"),
    url(r'^(?P<pk>\d+)/edit$', views.CaseEdit.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)$', views.CaseDetail.as_view(), name="detail"),
    url(r'^(?P<case_id>\d+)/add_permission$', views.PermissionCreate.as_view(), name="permission_create"),
    url(r'^permission/(?P<pk>\d+)/delete$', views.PermissionDelete.as_view(), name="permission_delete"),
    url(r'^permission/(?P<pk>\d+)/update$', views.PermissionUpdate.as_view(), name="permission_change"),

)
