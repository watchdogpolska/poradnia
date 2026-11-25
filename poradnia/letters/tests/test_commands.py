import os
import shutil
import tempfile
from io import StringIO

from django.core import mail
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings

from poradnia.letters.factories import AttachmentFactory, LetterFactory
from poradnia.letters.management.commands._find_orphaned_files_base import (
    FindOrphanedFilesBaseCommand,
)

from .test_utils import EML


class TempMediaRootMixin:
    """Point MEDIA_ROOT at a throwaway directory: these commands delete files."""

    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)
        media_override = override_settings(MEDIA_ROOT=self.media_root)
        media_override.enable()
        self.addCleanup(media_override.disable)

    def _write(self, rel_path, content=b"x"):
        abs_path = os.path.join(self.media_root, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(content)
        return abs_path

    def _mkdir(self, rel_path):
        abs_path = os.path.join(self.media_root, rel_path)
        os.makedirs(abs_path)
        return abs_path


class FindOrphanedAttachmentsCommandTestCase(TempMediaRootMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.attachment = AttachmentFactory()
        self.referenced = self.attachment.attachment.path
        self.orphan = self._write("letters/2020/1/1/abc/orphan.pdf")
        self.empty_dir = self._mkdir("letters/2020/2/2/empty")
        self.base_path = os.path.join(self.media_root, "letters")

    def test_referenced_file_is_inside_temp_media_root(self):
        self.assertTrue(self.referenced.startswith(self.media_root))

    def test_dry_run_deletes_nothing(self):
        call_command("find_orphaned_attachments")
        self.assertTrue(os.path.exists(self.referenced))
        self.assertTrue(os.path.exists(self.orphan))
        self.assertTrue(os.path.isdir(self.empty_dir))

    def test_delete_removes_orphans_and_empty_dirs_only(self):
        call_command("find_orphaned_attachments", "--delete")
        self.assertTrue(os.path.exists(self.referenced))
        self.assertFalse(os.path.exists(self.orphan))
        self.assertFalse(os.path.exists(self.empty_dir))
        # The base directory itself is never removed.
        self.assertTrue(os.path.isdir(self.base_path))

    def test_delete_leaves_messages_dir_alone(self):
        foreign = self._write("messages/not-an-attachment.eml")
        call_command("find_orphaned_attachments", "--delete")
        self.assertTrue(os.path.exists(foreign))

    def test_missing_base_path_is_a_no_op(self):
        shutil.rmtree(self.base_path)
        call_command("find_orphaned_attachments", "--delete")
        self.assertFalse(os.path.exists(self.base_path))

    def test_base_path_that_is_a_file_is_a_no_op(self):
        shutil.rmtree(self.base_path)
        self._write("letters")
        call_command("find_orphaned_attachments", "--delete")
        self.assertTrue(os.path.isfile(self.base_path))


class FindOrphanedEmlsCommandTestCase(TempMediaRootMixin, TestCase):
    def test_delete_removes_only_unreferenced_emls(self):
        letter = LetterFactory()
        referenced = letter.eml.path
        orphan = self._write("messages/orphan.eml")
        attachment_file = self._write("letters/2020/1/1/abc/file.pdf")

        call_command("find_orphaned_emls", "--delete")

        self.assertTrue(os.path.exists(referenced))
        self.assertFalse(os.path.exists(orphan))
        self.assertTrue(os.path.exists(attachment_file))


class FindOrphanedFilesBaseCommandTestCase(TestCase):
    def test_validate_configuration_lists_missing_attributes(self):
        with self.assertRaisesMessage(
            NotImplementedError,
            "queryset_model, queryset_field_name, base_subdir",
        ):
            FindOrphanedFilesBaseCommand()._validate_configuration()

    def test_get_file_size_of_missing_file_is_none(self):
        size = FindOrphanedFilesBaseCommand()._get_file_size(
            abs_path="/nonexistent/file", file_number=1
        )
        self.assertIsNone(size)


class UpdateLettersFromEmlsCommandTestCase(TempMediaRootMixin, TestCase):
    def test_rebuilds_html_from_eml_and_skips_letters_without_eml(self):
        with_eml = LetterFactory(html="")
        with_eml.eml.save("m.eml", ContentFile(EML))
        without_eml = LetterFactory(html="old", eml="")

        call_command("update_letters_from_emls", stdout=StringIO())

        with_eml.refresh_from_db()
        without_eml.refresh_from_db()
        self.assertIn("Café", with_eml.html)
        self.assertEqual(without_eml.html, "old")


class SendTestEmailToAdminsCommandTestCase(TestCase):
    @override_settings(ADMINS=[("Admin", "admin@example.com")])
    def test_sends_mail_to_admins(self):
        call_command("send_test_email_to_admins")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
        self.assertIn("poradnia.letters", mail.outbox[0].body)
