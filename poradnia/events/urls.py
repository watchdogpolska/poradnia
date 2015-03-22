from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^case-(?P<case_pk>\d+)$', views.add, name="add"),
    url(r'^event-(?P<pk>\d+)/edit$', views.edit, name="edit"),
    url(r'^event-(?P<pk>\d+)/dismiss$', views.dismiss, name="dismiss"),
)
