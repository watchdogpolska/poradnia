from django.views.generic import DetailView, ListView

from poradnia.advicer.models import Advice
from poradnia.cases.models import Case
from .models import JST


class JSTDetailView(DetailView):
    model = JST

    def get_context_data(self, **kwargs):
        context = super(JSTDetailView, self).get_context_data(**kwargs)
        context["advice_qs"] = (
            Advice.objects.for_user(self.request.user).area(self.object).all()
        )
        context["case_qs"] = (
            Case.objects.for_user(self.request.user).area(self.object).all()
        )
        return context


class JSTListView(ListView):
    model = JST

    def get_queryset(self):
        qs = super(JSTListView, self).get_queryset()
        return qs.voivodeship()
