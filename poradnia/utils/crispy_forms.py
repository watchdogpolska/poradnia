"""
Local crispy forms helpers to replace the unmaintained atom library.
This provides compatible replacements for the atom.ext.crispy_forms functionality.
"""
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib import messages
from django.forms import BaseFormSet
from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _


class FormsetHelper(FormHelper):
    """Base formset helper with common settings."""
    form_tag = False
    form_method = 'post'


class TableFormSetHelper(FormsetHelper):
    """
    Formset helper for table-based inline formsets.
    Uses bootstrap3 compatible template instead of the missing bootstrap template.
    """
    # Use the built-in bootstrap3 template instead of the missing 
    # bootstrap/table_inline_formset.html
    template = 'bootstrap3/table_inline_formset.html'


class TableFormSetMixin:
    """Mixin to add table formset helper to formsets."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = TableFormSetHelper()


class InlineTableFormSet(TableFormSetMixin, BaseInlineFormSet):
    """Inline formset with table helper."""
    pass


class TableFormSet(TableFormSetMixin, BaseFormSet):
    """Regular formset with table helper."""
    pass


class BaseTableFormSet(BaseInlineFormSet):
    """
    Base table formset compatible with the atom library version.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = TableFormSetHelper()


class HelperMixin:
    """Mixin to add form helper to forms."""
    form_helper_cls = FormHelper

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = getattr(self, 'helper', self.form_helper_cls(self))


class SingleButtonMixin(HelperMixin):
    """
    Dynamically add crispy button to form layout.
    
    Example:
        class PersonModelForm(SingleButtonMixin, forms.ModelForm):
            class Meta:
                model = Person
    """

    @property
    def action_text(self):
        """Text for the action submit button."""
        return _('Update') if hasattr(self, 'instance') and self.instance.pk else _('Save')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.add_input(Submit('action', self.action_text, css_class="btn-primary"))


class FormHorizontalMixin(HelperMixin):
    """Mixin to make forms horizontal with Bootstrap classes."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'


# View mixins
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
                                                     form=self.inline_form_cls,
                                                     formset=self.formset_cls)

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

    def get_formset_kwargs(self):
        return {}

    def form_valid(self, form):
        self.object = form.save(commit=False)
        FormSet = self.get_formset()
        formset = FormSet(self.request.POST or None,
                          self.request.FILES,
                          instance=self.object,
                          **self.get_formset_kwargs())

        if formset.is_valid():
            self.object.save()
            form.save_m2m()
            return self.formset_valid(form, formset)
        else:
            return self.formset_invalid(form, formset)