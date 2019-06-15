from django.views.generic import DetailView, ListView

from .models import JST


class JSTDetailView(DetailView):
    model = JST


class JSTListView(ListView):
    model = JST

    def get_queryset(self):
        qs = super(JSTListView, self).get_queryset()
        return qs.voivodeship()
