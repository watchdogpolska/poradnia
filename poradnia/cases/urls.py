from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
   url(r'^$', views.list, name="list"),
   url(r'^case-(?P<pk>\d+)/edit$', views.edit, name="edit"),
   url(r'^case-(?P<pk>\d+)/permission/add$', views.permission_add, name="permission_add"),
   url(r'^case-(?P<pk>\d+)/permission/update$', views.permission_update, name="permission_update"),
   url(r'^case-(?P<pk>\d+)$', views.detail, name="detail"),
)
