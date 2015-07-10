from django.http import HttpResponseRedirect
from django.contrib import messages


class DeleteMessageMixin(object):
    success_message = None
    hide_field = None

    def get_success_message(self):
        if self.success_message is None:
            raise NotImplementedError("Provide success_message or get_success_message")
        return self.success_message.format(**self.object.__dict__)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        if self.hide_field:
            setattr(self.object, self.hide_field, False)
            self.object.save()
        else:
            self.object.delete()
        messages.add_message(request, messages.SUCCESS, self.get_success_message())
        return HttpResponseRedirect(success_url)
