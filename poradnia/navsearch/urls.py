from django.conf.urls import url

from .views import AutocompleteView

urlpatterns = [
    url(r'^$', AutocompleteView.as_view(), name="navigation_autocomplete"),
]
