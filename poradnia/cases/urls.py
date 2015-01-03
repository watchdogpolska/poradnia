from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.CaseList.as_view(), name="list"),
    url(r'^user-(?P<username>\w+)$', views.CaseListUser.as_view(), name="list"),
    url(r'^tag-(?P<tag_pk>\w+)$', views.CaseListTag.as_view(), name="list"),
    url(r'^case-(?P<pk>\d+)/edit$', views.CaseEdit.as_view(), name="edit"),
    url(r'^case-(?P<pk>\d+)$', views.CaseDetail.as_view(), name="detail"),
    url(r'^free$', views.CaseListFree.as_view(), name="list_free"),
)
