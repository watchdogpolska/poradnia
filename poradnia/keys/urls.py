from django.urls import path

from . import views

urlpatterns = [
    path('', views.KeyListView.as_view(), name="list"),
    path('<int:pk>/', views.KeyDetailView.as_view(), name="details"),
    path('<int:pk>/usun/', views.KeyDeleteView.as_view(), name="delete"),
    path('stworz/', views.KeyCreateView.as_view(), name="create"),
]

app_name = 'poradnia.keys'