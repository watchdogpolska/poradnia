from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path("webhook", csrf_exempt(views.ReceiveEmailView.as_view()), name="webhook"),
    path("rejestr", views.LetterListView.as_view(), name="list"),
    path(
        "table/",
        views.cbv.LetterTableView.as_view(),
        name="table",
    ),
    path(
        "letters_table_ajax_data/",
        views.cbv.LetterAjaxDatatableView.as_view(),
        name="letters_table_ajax_data",
    ),
    path("sprawa-<int:case_pk>/", views.add, name="add"),
    path(
        "sprawa-<int:case_pk>/list-<int:letter_pk>/zalaczniki",
        views.StreamAttachmentView.as_view(),
        name="attachments_zip",
    ),
    path(
        "sprawa-<int:case_pk>/list-<int:letter_pk>/zalacznik/<int:pk>",
        views.DownloadAttachmentView.as_view(),
        name="attachment_download",
    ),
    path("<int:pk>/wyslij/", views.send, name="send"),
    path("<int:pk>/edytuj/", views.LetterUpdateView.as_view(), name="edit"),
    path("<int:pk>/", views.send, name="detail"),
    path("", views.NewCaseCreateView.as_view(), name="home"),
    path("", views.NewCaseCreateView.as_view(), name="add"),
    path("tinymce/", include("tinymce.urls")),
]

app_name = "poradnia.letters"
