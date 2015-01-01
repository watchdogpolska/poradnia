from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.add_letter, name='home'),
    url(r'^(?P<case_id>\d+)$', views.add_letter),

)
