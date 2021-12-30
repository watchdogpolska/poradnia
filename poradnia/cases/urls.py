from django.urls import path

from . import views

urlpatterns = [
    path("", views.CaseListView.as_view(), name="list"),
    path("sprawa-<int:pk>/edytuj/", views.CaseUpdateView.as_view(), name="edit"),
    path("sprawa-<int:pk>/zamknij/", views.CaseCloseView.as_view(), name="close"),
    path("sprawa-<int:pk>/scal/", views.CaseMergeView.as_view(), name="merge"),
    path(
        "sprawa-<int:pk>/uprawnienia/",
        views.UserPermissionCreateView.as_view(),
        name="permission_add",
    ),
    path(
        "sprawa-<int:pk>/uprawnienia-<username>/",
        views.UserPermissionUpdateView.as_view(),
        name="permission_update",
    ),
    path(
        "sprawa-<int:pk>/uprawnienia-<username>/~remove",
        views.UserPermissionRemoveView.as_view(),
        name="permission_remove",
    ),
    path(
        "sprawa-<int:pk>/uprawnienia/przyznaj/",
        views.CaseGroupPermissionView.as_view(),
        name="permission_grant",
    ),
    path("sprawa-<int:pk>/", views.CaseDetailView.as_view(), name="detail"),
    path("~autocomplete", views.CaseAutocomplete.as_view(), name="autocomplete"),
]

app_name = "poradnia.cases"
