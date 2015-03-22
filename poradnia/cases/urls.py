from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.list, name="list"),
    url(r'^case-(?P<pk>\d+)/edit$', views.edit, name="edit"),
    url(r'^case-(?P<pk>\d+)/permission$', views.permission, name="permission"),
    url(r'^case-(?P<pk>\d+)$', views.detail, name="detail"),
)
