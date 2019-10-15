from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.FeedbackListView.as_view(), name="list"),
    url(r'^submit$', views.FeedbackCreateView.as_view(), name="submit"),
    url(r'^(?P<pk>\d+)$', views.FeedbackDetailView.as_view(),
        name="details"),
    url(r'^(?P<pk>\d+)/update$', views.FeedbackStatusView.as_view(), name="status"),
]

app_name = 'poradnia.tasty_feedback'