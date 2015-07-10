

class FormInitialMixin(object):
    def get_initial(self, *args, **kwargs):
        initial = super(FormInitialMixin, self).get_initial(*args, **kwargs)
        initial.update(self.request.GET.dict())
        return initial
