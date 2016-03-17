from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.StatsIndexView.as_view(), name="index"),
    url(r'^api/sprawy/$', views.StatsCaseApiView.as_view(), name="case_stats_api"),
    url(r'^sprawy/$', views.StatsCaseView.as_view(), name="case_stats")
]
