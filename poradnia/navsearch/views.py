from django.db.models import Q
from django.views.generic import TemplateView
from cases.models import Case
from users.models import User


class AutocompleteView(TemplateView):
    template_name = 'navsearch/autocomplete.html'

    def get_context_data(self, *args, **kwargs):
        context = super(AutocompleteView, self).get_context_data(*args, **kwargs)
        q = self.request.GET.get('q', '')
        context = {'q': q}

        queries = {}
        queries['users'] = User.objects.for_user(self.request.user).filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        ).distinct()[:3]
        if q.replace('#', '').isdigit():
            queries['cases_id'] = (Case.objects.for_user(self.request.user).
                                   filter(id=q.replace('#', ''))[:3])
        queries['cases'] = (Case.objects.for_user(self.request.user).
                            filter(name__icontains=q)[:3])
        context.update(queries)
        return context
