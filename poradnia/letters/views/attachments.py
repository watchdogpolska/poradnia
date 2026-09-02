import zipfile
from os.path import basename

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, RedirectView

from poradnia.letters.models import Attachment
from poradnia.users.utils import PermissionMixin

ZIP_READ_CHUNK_SIZE = 64 * 1024


class _ZipStreamBuffer:
    """Write-only buffer standing in for zipfile.ZipFile's output file.

    zipfile falls back to a non-seekable write mode when fp.tell()/seek()
    aren't available, so a plain write() is all that's needed to make it
    emit the archive as a sequence of chunks instead of a real file.
    """

    def __init__(self):
        self._chunks = bytearray()

    def write(self, data):
        self._chunks += data
        return len(data)

    def flush(self):
        pass

    def take(self):
        chunk = bytes(self._chunks)
        self._chunks.clear()
        return chunk


def _iter_zip(attachments):
    buffer = _ZipStreamBuffer()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        for attachment in attachments:
            path = attachment.attachment.path
            with (
                open(path, "rb") as source,
                archive.open(basename(path), mode="w") as dest,
            ):
                while chunk := source.read(ZIP_READ_CHUNK_SIZE):
                    dest.write(chunk)
                    if data := buffer.take():
                        yield data
            if data := buffer.take():
                yield data
    if data := buffer.take():
        yield data


class StreamAttachmentView(PermissionMixin, ListView):
    model = Attachment

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(letter__case=self.kwargs["case_pk"]).filter(
            letter=self.kwargs["letter_pk"]
        )

    def render_to_response(self, context, **response_kwargs):
        response = StreamingHttpResponse(
            streaming_content=_iter_zip(self.object_list),
            content_type="application/zip",
        )
        response["Content-Disposition"] = (
            'attachment; filename="sprawa-{case_pk}-list-{letter_pk}.zip"'.format(
                **self.kwargs
            )
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
