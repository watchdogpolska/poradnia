from django.db.models import Q
from django.http import JsonResponse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views import View

from poradnia.cases.models import Case
from poradnia.users.models import User


class AutocompleteView(View):
    def get_user_queryset(self, q):
        return (
            User.objects.for_user(self.request.user)
            .filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
            )
            .distinct()[:3]
        )

    def get_item(self, row):
        return {"url": row.get_absolute_url(), "text": force_str(row)}

    def get_case_id_queryset(self, q):
        if q.replace("#", "").isdigit():
            return Case.objects.for_user(self.request.user).filter(
                id=q.replace("#", "")
            )[:3]
        return Case.objects.none()

    def get_case_queryset(self, q):
        return Case.objects.for_user(self.request.user).filter(name__icontains=q)[:3]

    def get(self, *args, **kwargs):
        q = self.request.GET.get("q")
        data = [] if not q else self.get_results(q)
        return JsonResponse({"results": data}, safe=False)

    def get_results(self, q):
        data = []
        data.append(
            {
                "text": _("Users"),
                "children": [self.get_item(x) for x in self.get_user_queryset(q)],
            }
        )
        data.append(
            {
                "text": _("Cases by ID"),
                "children": [self.get_item(x) for x in self.get_case_id_queryset(q)],
            }
        )
        data.append(
            {
                "text": _("Cases by name"),
                "children": [self.get_item(x) for x in self.get_case_queryset(q)],
            }
        )
        return data
