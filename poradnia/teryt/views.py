from django.views.generic import DetailView, ListView

from teryt_tree.dal_ext.views import CommunityAutocomplete
from poradnia.advicer.models import Advice
from poradnia.cases.models import Case
from .models import JST


class JSTDetailView(DetailView):
    model = JST

    def get_context_data(self, **kwargs):
        context = super(JSTDetailView, self).get_context_data(**kwargs)
        context['advice_qs'] = Advice.objects.for_user(
            self.request.user
        ).area(self.object).all()
        context['case_qs'] = Case.objects.for_user(
            self.request.user
        ).area(self.object).all()
        return context


class JSTListView(ListView):
    model = JST

    def get_queryset(self):
        qs = super(JSTListView, self).get_queryset()
        return qs.voivodeship()


class CommunityFullPathAutocomplete(CommunityAutocomplete):
    def get_result_label(self, result):
        """
        Include parent names in the label.

        Adds parent data after own label to keep searching by prefix intuitive.
        """
        own_label = super(CommunityFullPathAutocomplete, self).get_result_label(result)
        return "-".join([own_label] + self._get_parent_names(result))

    @staticmethod
    def _get_parent_names(obj):
        names = []
        current_node = obj
        for _ in range(5):  # add a hard limit in the (unlikely) case of cycles
            if current_node.parent:
                names.append(current_node.parent.name)
                current_node = current_node.parent
            else:
                break
        return names

