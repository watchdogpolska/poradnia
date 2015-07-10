from datetime import datetime
from django.views.generic import CreateView, DeleteView, ListView, DetailView, TemplateView
from django.core.urlresolvers import reverse_lazy as reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from braces.views import UserFormKwargsMixin
from users.mixins import PermissionMixin
from utilities.views import DeleteMessageMixin
from .models import Key
from .forms import KeyForm
from django.contrib import messages


class KeyCreateView(PermissionMixin, UserFormKwargsMixin, CreateView):
    form_class = KeyForm
    model = Key


class KeyDetailView(PermissionMixin, DetailView):
    model = Key

    def get_object(self, *args, **kwargs):
        obj = super(KeyDetailView, self).get_object(*args, **kwargs)
        obj.download_on = now()
        obj.save()
        messages.add_message(self.request, messages.SUCCESS,
            "{object} downloaded!".format(object=obj))
        return obj


class KeyDeleteView(PermissionMixin, DeleteMessageMixin, DeleteView):
    model = Key
    success_url = reverse('list')

    def get_success_message(self):
        return _(u"{object} deleted!").format(object=self.object)


class KeyListView(PermissionMixin, ListView):
    model = Key
