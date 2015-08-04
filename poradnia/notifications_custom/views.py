from django.views.generic import TemplateView
from braces.views import SelectRelatedMixin, PrefetchRelatedMixin, LoginRequiredMixin


class NotificationListView(SelectRelatedMixin, PrefetchRelatedMixin, LoginRequiredMixin,
        TemplateView):
    template_name = 'notifications/list.html'
    select_related = ['action_content_type', 'target_content_type', 'actor_content_type']
    prefetch_related = ['action_object', 'target', 'actor']
    paginate_by = 25

    def get_queryset(self, *args, **kwargs):
        return self.request.user.notifications
