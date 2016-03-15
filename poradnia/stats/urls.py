from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^api/sprawy/$', views.case_stats_api_view, name="case_stats_api"),
    url(r'^sprawy/$', views.StatsCaseView.as_view(), name="case_stats")
]
