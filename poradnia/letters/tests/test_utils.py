import gzip
from io import BytesIO

from django.core.files.base import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from poradnia.letters.models import Letter
from poradnia.letters.templatetags.format_text import format_text
from poradnia.letters.templatetags.letter_tags import file2css, letter2panel
from poradnia.letters.utils import (
    get_bytes_from_file,
    get_clean_email,
    get_html_from_eml_file,
)

EML = (
    b"From: a@example.com\r\n"
    b"To: b@example.com\r\n"
    b"Subject: Test\r\n"
    b"MIME-Version: 1.0\r\n"
    b'Content-Type: multipart/alternative; boundary="XX"\r\n'
    b"\r\n"
    b"--XX\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n"
    b"\r\n"
    b"plain part\r\n"
    b"--XX\r\n"
    b"Content-Type: text/html; charset=windows-1252\r\n"
    b"Content-Transfer-Encoding: quoted-printable\r\n"
    b"\r\n"
    b"<p>Caf=E9 =80</p>\r\n"
    b"--XX\r\n"
    b"Content-Type: text/html; charset=utf-8\r\n"
    b"Content-Transfer-Encoding: base64\r\n"
    b"\r\n"
    b"PHA+YmFzZTY0IPCfmIA8L3A+\r\n"
    b"--XX--\r\n"
)


class GetCleanEmailTestCase(SimpleTestCase):
    def test_plain_address_unchanged(self):
        self.assertEqual(get_clean_email("jan@example.com"), "jan@example.com")

    def test_strips_display_name(self):
        self.assertEqual(
            get_clean_email("Jan Kowalski <jan@example.com>"), "jan@example.com"
        )

    def test_takes_first_of_several(self):
        self.assertEqual(
            get_clean_email("<jan@example.com>, <ola@example.com>"),
            "jan@example.com",
        )


class GetBytesFromFileTestCase(SimpleTestCase):
    def test_uploaded_eml_returned_as_is(self):
        upload = SimpleUploadedFile("m.eml", EML)
        self.assertEqual(get_bytes_from_file(upload), EML)

    def test_django_file_eml_returned_as_is(self):
        self.assertEqual(get_bytes_from_file(File(BytesIO(EML), name="m.eml")), EML)

    def test_gzipped_eml_is_decompressed(self):
        upload = SimpleUploadedFile("m.eml.gz", gzip.compress(EML))
        self.assertEqual(get_bytes_from_file(upload), EML)

    def test_non_eml_non_gzip_returns_empty(self):
        upload = SimpleUploadedFile("m.bin", b"\x00\x01 not an e-mail")
        self.assertEqual(get_bytes_from_file(upload), b"")

    def test_unsupported_file_type_returns_empty(self):
        # The error log reads file.name, so the object needs one; a plain
        # BytesIO raises AttributeError instead of returning b"".
        stream = BytesIO(EML)
        stream.name = "m.eml"
        self.assertEqual(get_bytes_from_file(stream), b"")


class GetHtmlFromEmlFileTestCase(SimpleTestCase):
    def test_missing_file_returns_empty(self):
        self.assertEqual(get_html_from_eml_file(None), "")

    def test_empty_file_returns_empty(self):
        self.assertEqual(get_html_from_eml_file(SimpleUploadedFile("m.eml", b"")), "")

    def test_collects_html_parts_and_decodes_them(self):
        html = get_html_from_eml_file(SimpleUploadedFile("m.eml", EML))
        # windows-1252 quoted-printable part, then the base64 utf-8 part;
        # the text/plain part is skipped.
        self.assertIn("<p>Café €</p>", html)
        self.assertNotIn("plain part", html)
        # 4-byte characters are replaced for the utf8 (3-byte) MySQL columns.
        self.assertIn("<p>base64 (?)</p>", html)


class FormatTextTestCase(SimpleTestCase):
    @override_settings(RICH_TEXT_ENABLED=True)
    def test_rich_text_renders_markdown_and_sanitizes(self):
        html = format_text("**bold** <script>alert(1)</script>")
        self.assertIn("<strong>bold</strong>", html)
        self.assertNotIn("<script>", html)

    @override_settings(RICH_TEXT_ENABLED=False)
    def test_plain_text_uses_linebreaks_and_escapes(self):
        html = format_text("one\ntwo <b>")
        self.assertEqual(html, "<p>one<br>two &lt;b&gt;</p>")


class LetterTagsTestCase(SimpleTestCase):
    def _letter(self, genre, created_by_is_staff=False):
        return Letter(genre=genre, created_by_is_staff=created_by_is_staff)

    def test_letter2panel(self):
        self.assertEqual(letter2panel(self._letter(Letter.GENRE.comment)), "info")
        self.assertEqual(letter2panel(self._letter(Letter.GENRE.ai_message)), "success")
        self.assertEqual(
            letter2panel(self._letter(Letter.GENRE.ai_message_staff)), "success"
        )
        self.assertEqual(letter2panel(self._letter(Letter.GENRE.mail, True)), "primary")
        self.assertEqual(
            letter2panel(self._letter(Letter.GENRE.mail, False)), "default"
        )

    def test_file2css(self):
        self.assertEqual(file2css("letters/a/doc.pdf"), "far fa-file-pdf")
        self.assertEqual(file2css("x.docx"), "far fa-file-word")
        self.assertEqual(file2css("x.unknown"), "far fa-file")
        self.assertEqual(file2css("noextension"), "far fa-file")
