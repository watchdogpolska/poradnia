from __future__ import absolute_import
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _
from letters.forms import AddLetterForm
from events.forms import EventForm
from letters.helpers import formset_attachment_factory
from pagination_custom.utils import paginator
from letters.models import Letter
from records.models import Record
from ..models import Case
from ..readed.models import Readed
from ..tags.models import Tag
from ..forms import CaseForm


@login_required
def detail(request, pk):
    context = {}
    qs = (Case.objects.prefetch_related('tags').
          select_related('created_by').
          select_related('modified_by'))
    case = get_object_or_404(qs, pk=pk)
    case.view_perm_check(request.user)

    # Readed.update(user=request.user, case=case)

    context['object'] = case
    context['forms'] = {}
    context['forms']['letter'] = {'title': _('Letter'),
                                  'form': AddLetterForm(user=request.user, case=case),
                                  'formset': formset_attachment_factory()(instance=None)}
    context['forms']['event'] = {'title': _('Event'),
                                 'form': EventForm(user=request.user, case=case)}

    qs = (Record.objects.filter(case=case).
        select_related('letter__created_by', 'letter', 'letter__modified_by').
        prefetch_related('letter__attachment_set'))

    if not request.user.is_staff:
        qs = qs.filter(letter__status=Letter.STATUS.done)

    context['record_list'] = qs.all()
    return render(request, 'cases/case_detail.html', context)

SORT_MAP = {'deadline': 'deadline__time',
    'pk': 'pk',
    'client': 'client',
    'name': 'name',
    'last_response': 'last_response',
    'last_action': 'last_action'}


@login_required
def list(request):
    context = {}
    context['statuses'] = Case.STATUS
    object_list = (Case.objects.
                   # with_read_time(request.user).
                   for_user(request.user).
                   select_related('client').
                   prefetch_related('tags'))

    # # # Filtering 
    # TODO: Form or django-filter?
    # Show cases with TAG
    if 'tag' in request.GET:
        tag = get_object_or_404(Tag, pk=request.GET['tag'])
        object_list = object_list.filter(tags=tag)
        context['tag'] = tag

    # Show cases for CLIENT (USER)
    if 'user' in request.GET:
        user = get_user_model().objects.for_user(request.user)
        user = get_object_or_404(user, username=request.GET['user'])
        object_list = object_list.filter(client=user)
        context['user_filter'] = user

    # Show cases which has selected STATUS
    if 'status' in request.GET:
        object_list = object_list.filter(status=getattr(Case.STATUS, request.GET['status']))
        context['status'] = Case.STATUS[request.GET['status']]

    # Show cases which USER are involved
    if 'involved' in request.GET:
        user = get_user_model().objects.for_user(request.user)
        user = get_object_or_404(user, username=request.GET['user'])
        object_list = object_list.by_involved_in(user)
        context['involved'] = user

    # # # Ordering
    order_by = request.GET.get('order_by', 'deadline')  # get or default
    order_by = order_by if order_by in SORT_MAP else 'deadline'  # check exists
    order_key = SORT_MAP[order_by]  # get key
    ordering = 'asc' if request.GET.get('ordering') == 'asc' else 'desc'

    context['order_by'] = order_by
    context['ordering'] = ordering

    real_order_key = order_key if ordering == 'asc' else '-'+order_key

    object_list = object_list.order_by(real_order_key).all()
    context['object_list'] = paginator(request, object_list)

    return render(request, 'cases/case_list.html', context)


@login_required
def edit(request, pk):
    context = {}

    case = get_object_or_404(Case, pk=pk)
    case.perm_check(request.user, 'can_change_case')
    context['object'] = case

    if request.method == 'POST':
        form = CaseForm(request.POST, request.FILES, instance=case, user=request.user)
        if form.is_valid():
            obj = form.save()
            messages.success(request,  _('Successful add "%(object)s".') % {'object': obj})
            return redirect(obj)
    else:
        form = CaseForm(instance=case, user=request.user)
    context['form'] = form

    return render(request, 'cases/case_form.html', context)

