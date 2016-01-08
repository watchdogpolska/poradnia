from django.conf.urls import patterns, url

from .views import AutocompleteView

urlpatterns = patterns('',
    url(r'^$', AutocompleteView.as_view(), name="navigation_autocomplete"),
)
