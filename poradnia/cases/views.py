from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied
from guardian.forms import UserObjectPermissionsForm
from users.forms import ManageObjectPermissionForm
from letters.forms import AddLetterForm
from events.forms import EventForm
from letters.helpers import formset_attachment_factory
from pagination_custom.utils import paginator
from letters.models import Letter
from records.models import Record
from notifications import notify
from .models import Case
from .readed.models import Readed
from .tags.models import Tag
from .forms import CaseForm


@login_required
def detail(request, pk):
    context = {}
    qs = (Case.objects.prefetch_related('tags').
          select_related('created_by').
          select_related('modified_by'))
    case = get_object_or_404(qs, pk=pk)
    case.view_perm_check(request.user)

    Readed.update(user=request.user, case=case)

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


@login_required
def list(request):
    context = {}
    object_list = (Case.objects.
                   # with_read_time(request.user).
                   for_user(request.user).
                   select_related('client').
                   prefetch_related('tags'))

    # TODO: Form
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

    object_list = object_list.all()
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


@login_required
def permission(request, pk, limit='staff'):
    context = {}
    case = get_object_or_404(Case, pk=pk)
    context['object'] = case

    if case.status == case.STATUS.free:
        if not (request.user.has_perm('cases.can_assign')):
            raise PermissionDenied
    else:
        case.perm_check(request.user, 'can_manage_permission')

    # Update permission
    context['form'] = {}
    for user in case.get_users_with_perms():
        if request.method == 'POST':
            form = UserObjectPermissionsForm(user, case, request.POST or None, prefix=user.pk)
            if form.is_valid():
                form.save_obj_perms()
                messages.success(request,
                    _("Success updated permission of %(user)s to %(case)s") %
                    {'user': user, 'case': case})
        else:
            form = UserObjectPermissionsForm(user, case, request.POST or None, prefix=user.pk)
        context['form'][user] = form

    staff_only = True if limit == 'staff' else False
    context['staff_only'] = staff_only

    # Assign new permission
    form = ManageObjectPermissionForm(case, request.POST or None,
        staff_only=staff_only, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save_obj_perms()
            for user in form.cleaned_data['users']:
                notify.send(request.user, target=case, verb='granted', recipient=user)
                messages.success(request,
                    _("Success granted permission of %(user)s to %(case)s") %
                    {'user': user, 'case': case})
            if 'can_send_to_client' in form.cleaned_data[form.get_obj_perms_field_name()]:
                case.status = case.STATUS.open
                case.save()
    context['add_form'] = form

    return render(request, 'cases/case_form_permission.html', context)
