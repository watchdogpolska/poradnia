from braces.views import (
    FormValidMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SelectRelatedMixin,
    UserFormKwargsMixin,
)
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, DetailView
from django_filters.views import FilterView

from .models import Feedback
from .utils import get_filter, get_form


class FeedbackListView(
    LoginRequiredMixin, PermissionRequiredMixin, SelectRelatedMixin, FilterView
):
    permission_required = "tasty_feedback.view_feedback"
    filterset_class = get_filter()
    select_related = ["user"]
    paginate_by = 25
    model = Feedback


class FeedbackCreateView(
    LoginRequiredMixin, UserFormKwargsMixin, FormValidMessageMixin, CreateView
):
    model = Feedback
    form_class = get_form()

    def get_form_valid_message(self):
        return _("Feedback saved.")

    def get_success_url(self):
        referer_url = self.request.headers.get("referer", None)
        if referer_url:
            return referer_url
        else:
            return reverse("home")


class FeedbackDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = "tasty_feedback.view_feedback"
    model = Feedback


class FeedbackStatusView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "tasty_feedback.change_feedback"
    model = Feedback
    template_name_suffix = "_switch_status"
    success_url = reverse_lazy("tasty_feedback:list")

    def get_success_message(self):
        return _("%s updated") % (self.object)

    def delete(self, request, *args, **kwargs):
        """
        Update status the fetched object and then redirects to the success URL.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.status = not self.object.status
        self.object.save()
        messages.add_message(request, messages.SUCCESS, self.get_success_message())
        return HttpResponseRedirect(success_url)
