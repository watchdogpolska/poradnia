from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _
from .models import Event
from cases.models import Case
from .forms import EventForm


@login_required
def add(request, case_pk):
    context = {}

    case = get_object_or_404(Case, pk=case_pk)

    case.perm_check(request.user, 'can_add_record')
    context['case'] = case

    form = EventForm.partial(case=case, user=request.user)

    if request.method == 'POST':
        form = form(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request,
                _("Success added new event %(event)s") % {'event': obj, })
            return HttpResponseRedirect(case.get_absolute_url())
    else:
        form = form(user=request.user)
    context['form'] = form
    return render(request, 'events/form.html', context)


def edit(request, pk):
    context = {}

    event = get_object_or_404(Event, pk=pk)
    case = event.case

    case.perm_check(request.user, 'can_add_record')
    context['event'] = event
    context['object'] = case

    form = EventForm.partial(user=request.user, case=case, instance=event)

    if request.method == 'POST':
        form = form(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request,
                _("Success updated event %(event)s") % {'event': obj, })
            return HttpResponseRedirect(case.get_absolute_url())
    else:
        form = form(user=request.user, instance=event)
    context['form'] = form
    return render(request, 'events/form.html', context)


def dismiss(request, pk):
    pass
