from braces.views import LoginRequiredMixin


class PermissionMixin(LoginRequiredMixin, object):
    def get_queryset(self, *args, **kwargs):
        qs = super(PermissionMixin, self).get_queryset(*args, **kwargs)
        return qs.for_user(self.request.user)


class FormInitialMixin(object):
    def get_initial(self, *args, **kwargs):
        initial = super(FormInitialMixin, self).get_initial(*args, **kwargs)
        initial.update(self.request.GET.dict())
        return initial
