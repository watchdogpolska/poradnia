from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _
from teryt_tree.dal_ext.views import CountyAutocomplete, VoivodeshipAutocomplete

from . import views

urlpatterns = [
    re_path(_(r"^(?P<slug>[\w-]+)$"), views.JSTDetailView.as_view(), name="details"),
    path(_(""), views.JSTListView.as_view(), name="list"),
    path(_(""), views.JSTListView.as_view(), name="voivodeship"),
    path(
        _("voivodeship-autocomplete/"),
        VoivodeshipAutocomplete.as_view(),
        name="voivodeship-autocomplete",
    ),
    path(
        _("county-autocomplete/"),
        CountyAutocomplete.as_view(),
        name="county-autocomplete",
    ),
    path(
        _("community-autocomplete/"),
        views.AdviceCommunityAutocomplete.as_view(),
        name="community-autocomplete",
    ),
]

app_name = "poradnia.teryt"
