from os.path import basename

import zipstream
from django.http import StreamingHttpResponse
from django.views.generic import ListView, RedirectView
from poradnia.letters.models import Attachment
from poradnia.users.utils import PermissionMixin
from django.shortcuts import get_object_or_404


class StreamAttachmentView(PermissionMixin, ListView):
    model = Attachment

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(letter__case=self.kwargs["case_pk"]).filter(
            letter=self.kwargs["letter_pk"]
        )

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


class DownloadAttachmentView(PermissionMixin, RedirectView):
    model = Attachment

    def get_redirect_url(self, case_pk, letter_pk, pk):
        object = get_object_or_404(
            self.model.objects.filter(letter__case=case_pk).filter(letter=letter_pk),
            pk=pk,
        )
        return object.attachment.url
