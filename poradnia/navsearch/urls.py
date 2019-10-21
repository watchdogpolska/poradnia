from django.urls import path

from .views import AutocompleteView

urlpatterns = [path("", AutocompleteView.as_view(), name="navigation_autocomplete")]

app_name = "poradnia.navsearch"
