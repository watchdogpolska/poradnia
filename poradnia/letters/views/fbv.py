from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from cases.models import Case
from django.contrib import messages
from django.utils.translation import ugettext as _
from ..helpers import AttachmentFormSet
# from crispy_forms.helper import FormHelper
from ..forms import AddLetterForm, SendLetterForm
from ..models import Letter


REGISTRATION_TEXT = _("User  %(user)s registered! You will receive a password by mail. " +
    "Log in to get access to archive")


@login_required
def add(request, case_pk):
    context = {}
    case = get_object_or_404(Case, pk=case_pk)
    case.perm_check(request.user, 'can_add_record')

    LetterForm = AddLetterForm.partial(case=case, user=request.user)
    context['case'] = case

    formset = None
    if request.method == 'POST':
        form = LetterForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            formset = AttachmentFormSet(request.POST, request.FILES, instance=obj)
            if formset.is_valid():
                obj.save()
                messages.success(request, _("Letter %(object)s created!") % {'object': obj, })
                formset.save()
                return HttpResponseRedirect(case.get_absolute_url())
    else:
        form = LetterForm()
    context['form'] = form
    context['formset'] = formset or AttachmentFormSet(instance=None)
    context['headline'] = _('Add letter')
    return render(request, 'letters/form_add.html', context)


@login_required
def send(request, pk):
    context = {}

    letter = get_object_or_404(Letter, pk=pk)
    case = letter.case

    case.perm_check(request.user, 'can_add_record')
    context['object'] = letter
    context['case'] = case

    if letter.status == Letter.STATUS.done:
        messages.warning(request, _("It doesn't make sense."))
        return HttpResponseRedirect(case.get_absolute_url())

    LetterForm = SendLetterForm.partial(user=request.user, instance=letter)

    if request.method == 'POST':
        form = LetterForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request,
                _("Letter %(object)s send!") % {'object': obj, })
            obj.send_notification(actor=request.user, verb='accepted')
            return HttpResponseRedirect(case.get_absolute_url())
    else:
        form = SendLetterForm(user=request.user, instance=letter)
    context['form'] = form
    context['headline'] = _('Send to client')
    return render(request, 'letters/form_send.html', context)


def detail(request, pk):
    pass
