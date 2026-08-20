"""Local replacements for the unmaintained atom library's action/message
view and form mixins (see requirements/base.txt)."""

from functools import partial

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.views.generic.detail import (
    BaseDetailView,
    SingleObjectTemplateResponseMixin,
)


class FormInitialMixin:
    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        initial.update(self.request.GET.dict())
        return initial


class MessageMixin:
    success_message = None

    def get_success_message(self):
        if self.success_message is None:
            raise ImproperlyConfigured("Provide success_message or get_success_message")
        return self.success_message.format(**self.object.__dict__)


class DeleteMessageMixin:
    hide_field = None

    def get_success_message(self):
        template = dict(object=self.object, verbose_name=self.model._meta.verbose_name)
        return _("{verbose_name} {object} deleted!").format(**template)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        if self.hide_field:
            setattr(self.object, self.hide_field, False)
            self.object.save()
        else:
            self.object.delete()
        messages.add_message(request, messages.SUCCESS, self.get_success_message())
        return HttpResponseRedirect(success_url)


class ActionMixin:
    success_url = None

    def action(self):
        raise ImproperlyConfigured("No action to do. Provide a action body.")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.action()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        if not self.success_url:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return force_str(self.success_url).format(**self.object.__dict__)


class BaseActionView(ActionMixin, BaseDetailView):
    """Base view for action on an object. Subclass with a response mixin."""


class ActionView(SingleObjectTemplateResponseMixin, BaseActionView):
    template_name_suffix = "_action"


class ActionMessageMixin(MessageMixin):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.add_message(request, messages.SUCCESS, self.get_success_message())
        return response


class PartialMixin:
    """Lets a form class be pre-bound to constructor kwargs, e.g.
    SomeForm.partial(user=request.user)."""

    @classmethod
    def partial(cls, *args, **kwargs):
        return partial(cls, *args, **kwargs)


class AuthorMixin:
    def save(self, *args, **kwargs):
        if self.instance.pk:
            self.instance.modified_by = self.user
        else:
            self.instance.created_by = self.user
        return super().save(*args, **kwargs)
