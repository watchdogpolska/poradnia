from django.shortcuts import render
from django.views.generic import DetailView
from .models import Case

class Case_Detail(DetailView):
    model = Case
