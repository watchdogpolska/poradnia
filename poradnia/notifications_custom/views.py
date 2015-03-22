from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .utils import paginator


@login_required
def all(request):
    """
    Index page for authenticated user
    """
    qs = request.user.notifications
    qs = qs.prefetch_related('action_object').select_related('action_content_type')
    qs = qs.prefetch_related('target').select_related('target_content_type')
    qs = qs.prefetch_related('actor').select_related('actor_content_type').all()
    return render(request, 'notifications/list.html', {
        'page': paginator(request, qs.all())
    })
