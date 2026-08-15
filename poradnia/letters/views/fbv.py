import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from poradnia.cases.models import Case

# from crispy_forms.helper import FormHelper
from ..forms import AddLetterForm, AttachmentsFieldForm, SendLetterForm
from ..models import Letter

NEW_CASE_ANONYMOUS_TEXT = _(
    "Thank you for submitting your case. Please check your e-mail for "
    "further instructions on how to proceed."
)

logger = logging.getLogger(__name__)


@login_required
def add(request, case_pk):
    context = {}
    case = get_object_or_404(Case, pk=case_pk)
    case.perm_check(request.user, "can_add_record")

    LocalLetterForm = AddLetterForm.partial(case=case, user=request.user)
    context["case"] = case

    if request.method == "POST":
        form = LocalLetterForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            messages.success(request, _("Letter %(object)s created!") % {"object": obj})
            logger.info(f"Letter {obj.id} created by {request.user}")
            obj.send_notification(actor=request.user, verb="created")
            return HttpResponseRedirect(case.get_absolute_url())
    else:
        form = LocalLetterForm()
    context["form"] = form
    context["attachments_form"] = AttachmentsFieldForm()
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
