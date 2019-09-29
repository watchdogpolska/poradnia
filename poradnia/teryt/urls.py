# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _
from teryt_tree.dal_ext.views import (CommunityAutocomplete,
                                      CountyAutocomplete,
                                      VoivodeshipAutocomplete)

from . import views

urlpatterns = [
    url(_(r'^(?P<slug>[\w-]+)$'), views.JSTDetailView.as_view(), name="details"),
    url(_(r'^$'), views.JSTListView.as_view(), name="list"),
    url(_(r'^$'), views.JSTListView.as_view(), name="voivodeship"),
    url(_(r'^voivodeship-autocomplete/$'), VoivodeshipAutocomplete.as_view(),
        name='voivodeship-autocomplete', ),
    url(_(r'^county-autocomplete/$'), CountyAutocomplete.as_view(),
        name='county-autocomplete', ),
    url(_(r'^community-autocomplete/$'), CommunityAutocomplete.as_view(),
        name='community-autocomplete', ),
    url(_(r'^community-full-path-autocomplete/$'), views.CommunityFullPathAutocomplete.as_view(),
        name='community-full-path-autocomplete', ),
]

app_name = 'poradnia.teryt'
