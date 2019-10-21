from django.urls import path

from poradnia.judgements import views

urlpatterns = [
    path('~create-<int:case_pk>', views.CourtCaseCreateView.as_view(),
        name="create"),
    path('courtcase-<int:pk>/~update', views.CourtCaseUpdateView.as_view(),
        name="update"),
    path('courtcase-<int:pk>/~delete', views.CourtCaseDeleteView.as_view(),
        name="delete"),
]

app_name = 'poradnia.judgements'