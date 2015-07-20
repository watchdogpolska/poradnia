from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^/$', views.KeyListView.as_view(), name="list"),
    url(r'^/(?P<pk>\d+)$', views.KeyDetailView.as_view(), name="details"),
    url(r'^/(?P<pk>\d+)/delete$', views.KeyDeleteView.as_view(), name="delete"),
    url(r'^/create$', views.KeyCreateView.as_view(), name="create"),
)
