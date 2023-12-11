from dal import autocomplete
from django.views.generic import DetailView, ListView

from poradnia.advicer.models import Advice
from poradnia.cases.models import Case

from .models import JST


class JSTDetailView(DetailView):
    model = JST

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["advice_qs"] = (
            Advice.objects.for_user(self.request.user).area_filter(self.object).all()
        )
        context["case_qs"] = (
            Case.objects.for_user(self.request.user).area_filter(self.object).all()
        )
        return context


class JSTListView(ListView):
    model = JST

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.voivodeship()


class AdviceCommunityAutocomplete(autocomplete.Select2QuerySetView):
    def get_result_label(self, result):
        return result.tree_name

    def get_queryset(self):
        qs = JST.objects.community().select_related("category").all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        county = self.forwarded.get("county", None)
        if county:
            return qs.filter(parent=county)
        return qs
