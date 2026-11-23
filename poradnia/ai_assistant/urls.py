from django.urls import path

from .views import (
    N8nArticlesSearchCallbackView,
    N8nCaseTagsCallbackView,
    N8nSimilarCasesCallbackView,
)

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
    path(
        "api/similar-cases",
        N8nSimilarCasesCallbackView.as_view(),
        name="similar-cases-callback",
    ),
]
