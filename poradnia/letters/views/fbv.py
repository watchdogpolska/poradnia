import logging

from django.contrib import messages
from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from poradnia.cases.models import Case

# from crispy_forms.helper import FormHelper
from ..forms import AddLetterForm, SendLetterForm
from ..helpers import AttachmentFormSet
from ..models import Letter

REGISTRATION_TEXT = _(
    "User  %(user)s registered! You will receive a password by mail. "
    + "Log in to get access to archive"
)

logger = logging.getLogger(__name__)


@login_required
def add(request, case_pk):
    context = {}
    case = get_object_or_404(Case, pk=case_pk)
    case.perm_check(request.user, "can_add_record")

    LocalLetterForm = AddLetterForm.partial(case=case, user=request.user)
    context["case"] = case

    formset = None
    if request.method == "POST":
        form = LocalLetterForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            formset = AttachmentFormSet(request.POST, request.FILES, instance=obj)
            if formset.is_valid():
                obj.save()
                content_type = ContentType.objects.get_for_model(Letter)
                change_dict = {
                    "changed": form.changed_data,
                    "cleaned_data": form.cleaned_data,
                }
                LogEntry.objects.log_action(
                    user_id=request.user.id,
                    content_type_id=content_type.id,
                    object_id=obj.id,
                    object_repr=str(obj),
                    action_flag=ADDITION,
                    change_message=f"{change_dict}",
                )
                messages.success(
                    request, _("Letter %(object)s created!") % {"object": obj}
                )
                logger.info(f"Letter {obj.id} created by {request.user}")
                formset.save()
                obj.send_notification(actor=request.user, verb="created")
                return HttpResponseRedirect(case.get_absolute_url())
    else:
        form = LocalLetterForm()
    context["form"] = form
    context["formset"] = formset or AttachmentFormSet(instance=None)
    context["headline"] = _("Add letter")
    return render(request, "letters/form_add.html", context)


@login_required
def send(request, pk):
    context = {}

    letter = get_object_or_404(Letter, pk=pk)
    case = letter.case

    case.perm_check(request.user, "can_add_record")
    context["object"] = letter
    context["case"] = case

    if letter.status == Letter.STATUS.done:
        messages.warning(request, _("You can not send one letter twice."))
        return HttpResponseRedirect(case.get_absolute_url())

    LetterForm = SendLetterForm.partial(user=request.user, instance=letter)

    if request.method == "POST":
        form = LetterForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, _("Letter %(object)s send!") % {"object": obj})
            return HttpResponseRedirect(case.get_absolute_url())
    else:
        form = SendLetterForm(user=request.user, instance=letter)
    context["form"] = form
    context["headline"] = _("Send to client")
    return render(request, "letters/form_send.html", context)


def detail(request, pk):
    pass
