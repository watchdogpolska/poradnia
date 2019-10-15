
from django.conf.urls import url

from poradnia.users import views

urlpatterns = [
    # URL pattern for the UserListView  # noqa
    url(
        regex=r'^$',
        view=views.UserListView.as_view(),
        name='list'
    ),
    # URL pattern for the UserRedirectView
    url(
        regex=r'^~przekieruj/$',
        view=views.UserRedirectView.as_view(),
        name='redirect'
    ),
    # URL pattern for the UserDetailView
    url(
        regex=r'^(?P<username>[\w.@+-]+)/$',
        view=views.UserDetailView.as_view(),
        name='detail'
    ),
    # URL pattern for the UserUpdateView
    url(
        regex=r'^~aktualizuj/$',
        view=views.UserUpdateView.as_view(),
        name='update'
    ),
    # URL pattern for the ProfileUpdateView
    url(
        regex=r'^~profil/$',
        view=views.ProfileUpdateView.as_view(),
        name='profile'
    ),
    url(
        regex=r'^~autocomplete/$',
        view=views.UserAutocomplete.as_view(),
        name='autocomplete'
    ),
]
