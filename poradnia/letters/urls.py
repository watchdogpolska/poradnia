from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.NewCaseCreateView.as_view(), name='home'),
    url(r'^$', views.NewCaseCreateView.as_view(), name='add'),
    url(r'^rejestr$', views.LetterListView.as_view(), name='list'),
    url(r'^sprawa-(?P<case_pk>\d+)/$', views.add, name="add"),
    url(r'^(?P<pk>\d+)/wyslij/$', views.send, name="send"),
    url(r'^(?P<pk>\d+)/edytuj/$', views.LetterUpdateView.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/$', views.send, name="detail"),
)
