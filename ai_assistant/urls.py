from django.urls import path

from .views import N8nArticlesSearchCallbackView

app_name = "ai_assistant"

urlpatterns = [
    path(
        "api/articles",
        N8nArticlesSearchCallbackView.as_view(),
        name="articles-callback",
    ),
]
