from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from poradnia.users.utils import PermissionMixin

from ..models import Letter


class LetterAiSearchAcceptView(PermissionMixin, SingleObjectMixin, View):
    model = Letter
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.case.perm_check(request.user, "can_change_case")

        search_request = self.object.get_ai_search_request()
        if search_request is not None and search_request.rejected_at is None:
            search_request.accepted_by = request.user
            search_request.accepted_at = timezone.now()
            search_request.save(update_fields=["accepted_by", "accepted_at", "updated_at"])
        return render(
            request, "letters/_letter_ai_feedback.html", {"object": self.object}
        )


class LetterAiSearchRejectView(PermissionMixin, SingleObjectMixin, View):
    model = Letter
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.case.perm_check(request.user, "can_change_case")

        reason = (request.POST.get("rejection_reason") or "").strip()
        if not reason:
            return HttpResponseBadRequest("rejection_reason is required")

        search_request = self.object.get_ai_search_request()
        if search_request is not None and search_request.accepted_at is None:
            search_request.rejected_by = request.user
            search_request.rejected_at = timezone.now()
            search_request.rejection_reason = reason
            search_request.save(
                update_fields=[
                    "rejected_by",
                    "rejected_at",
                    "rejection_reason",
                    "updated_at",
                ]
            )
        return render(
            request, "letters/_letter_ai_feedback.html", {"object": self.object}
        )
