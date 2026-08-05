from django.urls import path

from . import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="index"),
    path("cases/", views.CasesTabView.as_view(), name="cases_tab"),
    path("advices/", views.AdvicesTabView.as_view(), name="advices_tab"),
    path("judgements/", views.JudgementsTabView.as_view(), name="judgements_tab"),
]

app_name = "poradnia.dashboard"
