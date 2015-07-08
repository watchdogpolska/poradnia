from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from users.forms import TranslatedManageObjectPermissionForm, TranslatedUserObjectPermissionsForm
from ..models import Case



@login_required
def permission_add(request, pk):
    context = {}
    case = get_object_or_404(Case, pk=pk)
    context['object'] = case

    if case.status == case.STATUS.free:
        if not (request.user.has_perm('cases.can_assign')):
            raise PermissionDenied
    else:
        case.perm_check(request.user, 'can_manage_permission')

    # Assign new permission
    form = TranslatedManageObjectPermissionForm(case, request.POST or None, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save_obj_perms()
            for user in form.cleaned_data['users']:
                user.notify(actor=request.user, target=case, verb='granted', from_email=case.get_email())
                messages.success(request,
                    _("Success granted permission of %(user)s to %(case)s") %
                    {'user': user, 'case': case})
            case.status_update()
    context['add_form'] = form

    return render(request, 'cases/case_form_permission_add.html', context)


@login_required
def permission_update(request, pk):
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
        form = TranslatedUserObjectPermissionsForm(user, case, request.POST or None, prefix=user.pk)
        if request.method == 'POST':
            if form.is_valid():
                form.save_obj_perms()
                messages.success(request,
                    _("Success updated permission of %(user)s to %(case)s") %
                    {'user': user, 'case': case})
            case.status_update()
        context['form'][user] = form

    return render(request, 'cases/case_form_permission_update.html', context)
