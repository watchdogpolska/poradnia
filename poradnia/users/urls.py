from django.urls import path, re_path

from poradnia.users import views

urlpatterns = [
    path("", views.UserListView.as_view(), name="list"),
    re_path(r"^~przekieruj/$", views.UserRedirectView.as_view(), name="redirect"),
    re_path(
        r"^(?P<username>[\w.@+-]+)/$",
        views.UserDetailView.as_view(),
        name="detail",
    ),
    path("info/<username>/", views.UserInfoView.as_view(), name="user_info"),
    re_path(
        r"^(?P<username>[\w.@+-]+)/~deassign/$",
        views.UserDeassignView.as_view(),
        name="deassign",
    ),
    re_path(r"^~aktualizuj/$", views.UserUpdateView.as_view(), name="update"),
    re_path(r"^~profil/$", views.ProfileUpdateView.as_view(), name="profile"),
    re_path(
        r"^~autocomplete/$",
        views.UserAutocomplete.as_view(),
        name="autocomplete",
    ),
]

app_name = "poradnia.users"
