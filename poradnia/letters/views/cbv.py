from ..models import Letter
from django.views.generic import CreateView
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.http import HttpResponseRedirect
from braces.views import UserFormKwargsMixin, SetHeadlineMixin
from ..forms import NewCaseForm
from .fbv import REGISTRATION_TEXT


class NewCaseCreateView(SetHeadlineMixin, UserFormKwargsMixin, CreateView):
    model = Letter
    form_class = NewCaseForm
    headline = _('Create a new case')
    template_name = 'letters/form_new.html'

    def form_valid(self, form, *args, **kwargs):
        self.object = form.save()
        messages.success(self.request,
            _("Case about %(object)s created!") % {'object': self.object.name, })
        if self.object.created_by != self.object.client:
            self.obj.client.notify(actor=self.request.user, verb='created', target=self.object,
                from_email=self.object.case.get_email())
        if self.request.user.is_anonymous():
            messages.success(self.request, _(REGISTRATION_TEXT) % {'user': self.object.created_by})
        return HttpResponseRedirect(self.object.case.get_absolute_url())
