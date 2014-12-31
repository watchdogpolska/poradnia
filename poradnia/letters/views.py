from django.shortcuts import render
from django.views.generic.edit import FormView
from .forms import LetterForm


class ContactView(FormView):
    template_name = 'letter.html'
    form_class = LetterForm
    success_url = '/thanks/'
