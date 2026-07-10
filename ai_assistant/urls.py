from django.urls import path

from .views import N8nArticlesSearchCallbackView, N8nCaseTagsCallbackView

app_name = "ai_assistant"

urlpatterns = [
    path(
        "api/articles",
        N8nArticlesSearchCallbackView.as_view(),
        name="articles-callback",
    ),
    path(
        "api/case-tags",
        N8nCaseTagsCallbackView.as_view(),
        name="case-tags-callback",
    ),
]
