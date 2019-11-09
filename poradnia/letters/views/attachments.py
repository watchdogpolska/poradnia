from os.path import basename

import zipstream
from django.http import StreamingHttpResponse
from django.views.generic import ListView

from poradnia.letters.models import Attachment
from poradnia.users.utils import PermissionMixin


class StreamAttachmentView(PermissionMixin, ListView):
    model = Attachment

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(letter__case=self.kwargs["case_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        z = zipstream.ZipFile()
        for attachment in self.get_queryset():
            z.write(attachment.attachment.path, basename(attachment.attachment.path))
        context["archive"] = z
        return context

    def render_to_response(self, context, **response_kwargs):
        response = StreamingHttpResponse(
            streaming_content=context["archive"], content_type="application/zip"
        )
        response[
            "Content-Disposition"
        ] = 'attachment; filename="sprawa-{case_pk}-list-{letter_pk}.zip"'.format(
            **self.kwargs
        )
        return response
