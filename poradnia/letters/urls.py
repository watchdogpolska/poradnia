from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^/$', views.new_case, name='home'),
    url(r'^/$', views.new_case, name='add'),
    url(r'^case-(?P<case_pk>\d+)/add$', views.add, name="add"),
    url(r'^-(?P<pk>\d+)/detail$', views.send, name="detail"),
    url(r'^-(?P<pk>\d+)/send$', views.send, name="send"),
    url(r'^-(?P<pk>\d+)/edit$', views.edit, name="edit"),
)
