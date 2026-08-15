from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _

from . import views

urlpatterns = [
    re_path(_(r"^(?P<slug>[\w-]+)$"), views.JSTDetailView.as_view(), name="details"),
    path("", views.JSTListView.as_view(), name="list"),
    path("", views.JSTListView.as_view(), name="voivodeship"),
    path(
        _("community-autocomplete/"),
        views.AdviceCommunityAutocomplete.as_view(),
        name="community-autocomplete",
    ),
]

app_name = "poradnia.teryt"
