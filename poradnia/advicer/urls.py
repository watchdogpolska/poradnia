from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.AdviceList.as_view(), name='list'),
    url(r'^nowa/$', views.AdviceCreate.as_view(), name="create"),
    url(r'^(?P<pk>\d+)$', views.AdviceDetail.as_view(), name="detail"),
    url(r'^(?P<pk>\d+)/edytuj/$', views.AdviceUpdate.as_view(), name="update"),
    url(r'^(?P<pk>\d+)/usun/$', views.AdviceDelete.as_view(), name="delete"),
]
