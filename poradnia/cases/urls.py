from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.CaseList.as_view(), name="list"),
    url(r'^user-(?P<username>\w+)$', views.CaseListClient.as_view(), name="list"),
    url(r'^tag-(?P<tag_pk>\w+)$', views.CaseListClient.as_view(), name="list"),
    url(r'^(?P<pk>\d+)/edit$', views.CaseEdit.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)$', views.CaseDetail.as_view(), name="detail"),
)
