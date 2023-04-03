from django.urls import path

from . import views

urlpatterns = [
    path("", views.AdviceList.as_view(), name="list"),
    path(
        "table/",
        views.AdviceTableView.as_view(),
        name="table",
    ),
    path(
        "advice_table_ajax_data/",
        views.AdviceAjaxDatatableView.as_view(),
        name="advice_table_ajax_data",
    ),
    path("nowa/", views.AdviceCreate.as_view(), name="create"),
    path("<int:pk>", views.AdviceDetail.as_view(), name="detail"),
    path("<int:pk>/edytuj/", views.AdviceUpdate.as_view(), name="update"),
    path("<int:pk>/usun/", views.AdviceDelete.as_view(), name="delete"),
    path(
        "issue-autocomplete/",
        views.IssueAutocomplete.as_view(),
        name="issue-autocomplete",
    ),
    path(
        "area-autocomplete/", views.AreaAutocomplete.as_view(), name="area-autocomplete"
    ),
]

app_name = "poradnia.advicer"
