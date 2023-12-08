from atom.views import DeleteMessageMixin
from braces.views import UserFormKwargsMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView

from poradnia.users.utils import PermissionMixin, SuperuserPermissionMixin

from .forms import KeyForm
from .models import Key


class KeyCreateView(
    SuperuserPermissionMixin, PermissionMixin, UserFormKwargsMixin, CreateView
):
    form_class = KeyForm
    model = Key


class KeyDetailView(SuperuserPermissionMixin, PermissionMixin, DetailView):
    model = Key

    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        obj.download_on = now()
        obj.save()
        messages.add_message(
            self.request, messages.SUCCESS, "{object} downloaded!".format(object=obj)
        )
        return obj


class KeyDeleteView(
    SuperuserPermissionMixin, PermissionMixin, DeleteMessageMixin, DeleteView
):
    model = Key
    success_url = reverse_lazy("list")

    def get_success_message(self):
        return _("{object} deleted!").format(object=self.object)


class KeyListView(SuperuserPermissionMixin, PermissionMixin, ListView):
    model = Key
