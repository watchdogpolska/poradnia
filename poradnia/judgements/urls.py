from django.conf.urls import url

from poradnia.judgements import views

urlpatterns = [
    url(r'^~create-(?P<case_pk>\d+)$', views.CourtCaseCreateView.as_view(),
        name="create"),
    url(r'^courtcase-(?P<pk>\d+)/~update$', views.CourtCaseUpdateView.as_view(),
        name="update"),
    url(r'^courtcase-(?P<pk>\d+)/~delete$', views.CourtCaseDeleteView.as_view(),
        name="delete"),
]

app_name = 'poradnia.judgements'