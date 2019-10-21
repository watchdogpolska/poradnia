from django.urls import path

from . import views

urlpatterns = [
    path('', views.FeedbackListView.as_view(), name="list"),
    path('submit', views.FeedbackCreateView.as_view(), name="submit"),
    path('<int:pk>', views.FeedbackDetailView.as_view(),
        name="details"),
    path('<int:pk>/update', views.FeedbackStatusView.as_view(), name="status"),
]

app_name = 'poradnia.tasty_feedback'