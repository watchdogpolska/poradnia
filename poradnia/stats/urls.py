from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sprawy/$', views.case_stats_view, name="case_stats")
]
