from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.KeyListView.as_view(), name="list"),
    url(r'^(?P<pk>\d+)/$', views.KeyDetailView.as_view(), name="details"),
    url(r'^(?P<pk>\d+)/usun/$', views.KeyDeleteView.as_view(), name="delete"),
    url(r'^stworz/$', views.KeyCreateView.as_view(), name="create"),
]
