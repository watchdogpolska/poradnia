from django.http import HttpResponseRedirect
from django.contrib import messages
from utilities.forms import BaseTableFormSet
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext as _


class FormInitialMixin(object):
    def get_initial(self, *args, **kwargs):
        initial = super(FormInitialMixin, self).get_initial(*args, **kwargs)
        initial.update(self.request.GET.dict())
        return initial


class DeleteMessageMixin(object):
    success_message = None
    hide_field = None

    def get_success_message(self):
        if self.success_message is None:
            raise NotImplementedError("Provide success_message or get_success_message")
        return self.success_message.format(**self.object.__dict__)

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


class FormSetMixin(object):
    inline_model = None
    inline_form_cls = None
    formset_cls = BaseTableFormSet
    formset = None  # precomputed by default

    def get_instance(self):
        return None

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_formset(self):
        return self.formset or inlineformset_factory(self.model, self.inline_model,
            form=self.inline_form_cls, formset=self.formset_cls)

    def get_context_data(self, **kwargs):
        context = super(FormSetMixin, self).get_context_data(**kwargs)
        context.update({'formset': self.get_formset()(instance=self.get_instance())})
        return context

    def get_formset_valid_message(self):
        return _("{0} created!").format(self.object)

    def get_form(self, *args, **kwargs):
        form = super(FormSetMixin, self).get_form(*args, **kwargs)
        if hasattr(form, 'helper'):
            form.helper.form_tag = False
        return form

    def formset_valid(self, form, formset):
        formset.save()
        messages.success(self.request, self.get_formset_valid_message())
        return HttpResponseRedirect(self.get_success_url())

    def formset_invalid(self, form, formset):
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def form_valid(self, form):
        self.object = form.save(commit=False)
        FormSet = self.get_formset()
        formset = FormSet(self.request.POST or None, self.request.FILES, instance=self.object)

        if formset.is_valid():
            self.object.save()
            return self.formset_valid(form, formset)
        else:
            return self.formset_invalid(form, formset)
