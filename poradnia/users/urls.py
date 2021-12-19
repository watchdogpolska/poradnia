from django.conf.urls import url

from poradnia.users import views

urlpatterns = [
    url(r"^$", views.UserListView.as_view(), name="list"),
    url(r"^~przekieruj/$", views.UserRedirectView.as_view(), name="redirect"),
    url(
        r"^(?P<username>[\w.@+-]+)/$",
        views.UserDetailView.as_view(),
        name="detail",
    ),
    url(r"^(?P<username>[\w.@+-]+)/~deassign/$", views.UserDeassignView.as_view(), name="deassign"),
    url(r"^~aktualizuj/$", views.UserUpdateView.as_view(), name="update"),
    url(r"^~profil/$", views.ProfileUpdateView.as_view(), name="profile"),
    url(
        r"^~autocomplete/$",
        views.UserAutocomplete.as_view(),
        name="autocomplete",
    ),
]

app_name = "poradnia.users"
