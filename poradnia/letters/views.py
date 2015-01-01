from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import LetterForm


def add_letter(request, case_id=None):
    if request.method == 'POST':
        form = LetterForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(case_id=case_id)
            return HttpResponseRedirect(obj.case.get_absolute_url())
    else:
        form = LetterForm(user=request.user)
    return render(request, 'letters/form.html', {'form': form})
