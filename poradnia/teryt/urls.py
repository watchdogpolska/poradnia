from django.urls import re_path
from django.utils.translation import gettext_lazy as _
from teryt_tree.dal_ext.views import (
    CommunityAutocomplete,
    CountyAutocomplete,
    VoivodeshipAutocomplete,
)

from . import views

urlpatterns = [
    re_path(_(r"^(?P<slug>[\w-]+)$"), views.JSTDetailView.as_view(), name="details"),
    re_path(_(r"^$"), views.JSTListView.as_view(), name="list"),
    re_path(_(r"^$"), views.JSTListView.as_view(), name="voivodeship"),
    re_path(
        _(r"^voivodeship-autocomplete/$"),
        VoivodeshipAutocomplete.as_view(),
        name="voivodeship-autocomplete",
    ),
    re_path(
        _(r"^county-autocomplete/$"),
        CountyAutocomplete.as_view(),
        name="county-autocomplete",
    ),
    re_path(
        _(r"^community-autocomplete/$"),
        CommunityAutocomplete.as_view(),
        name="community-autocomplete",
    ),
]

app_name = "poradnia.teryt"
