from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)$', views.Case_Details.as_view(), name="details"),

)
