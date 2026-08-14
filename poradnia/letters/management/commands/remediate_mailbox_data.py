import hashlib
import logging
import os

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django_mailbox.models import Mailbox, Message, MessageAttachment

from poradnia.letters.models import Letter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "One-off remediation to run before django_mailbox is uninstalled. "
        "Some historical Letters share their .eml file on disk with the "
        "django_mailbox Message they were created from (Letter.eml and "
        "Message.eml point at the same path). For each such Letter, this "
        "materializes an independent copy of the file and clears "
        "Letter.message. If the shared file is missing on disk, "
        "Letter.eml is left untouched and only the message link is "
        "cleared. Once no Letter references django_mailbox any "
        "more, it deletes all django_mailbox data (Mailbox, Message, "
        "MessageAttachment) and their files. Safe to re-run: only Letters "
        "with `message` still set are touched, and the purge only runs "
        "once none remain."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually write changes and delete django_mailbox data. "
            "Without this flag, only reports what would happen.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        logger.info("Mode: %s", "APPLY" if apply_changes else "DRY-RUN")

        letters = Letter.objects.filter(message__isnull=False).select_related(
            "message"
        )
        total = letters.count()
        logger.info("Letters still linked to django_mailbox: %s", total)

        failed = 0
        missing_eml = 0
        for letter in letters:
            try:
                if self._detach_letter(letter, apply_changes):
                    missing_eml += 1
            except Exception:
                failed += 1
                logger.exception("Failed to detach letter pk=%s", letter.pk)

        detached = total - failed
        logger.info(
            "Detached: %s (%s with missing eml file, unlinked without "
            "copying), failed: %s",
            detached,
            missing_eml,
            failed,
        )

        if failed:
            raise CommandError(
                f"{failed} letter(s) failed detachment; django_mailbox data "
                "was NOT purged. Fix the errors above and re-run."
            )

        if apply_changes:
            remaining = Letter.objects.filter(message__isnull=False).count()
            if remaining:
                logger.warning(
                    "%s letter(s) still linked to django_mailbox; "
                    "skipping purge.",
                    remaining,
                )
                return

        self._purge_mailbox_data(apply_changes)

    def _detach_letter(self, letter, apply_changes):
        message = letter.message
        shares_file = bool(
            letter.eml and message.eml and letter.eml.name == message.eml.name
        )

        logger.info(
            "Letter pk=%s message_id=%s shares_eml_file=%s",
            letter.pk,
            message.pk,
            shares_file,
        )

        missing_eml = False
        if shares_file:
            try:
                with letter.eml.storage.open(letter.eml.name, "rb") as f:
                    source_bytes = f.read()
            except FileNotFoundError:
                missing_eml = True
                logger.warning(
                    "Letter pk=%s: eml file %r is missing on disk; leaving "
                    "Letter.eml unchanged and unlinking the django_mailbox "
                    "message without copying it.",
                    letter.pk,
                    letter.eml.name,
                )
            else:
                source_hash = hashlib.sha256(source_bytes).hexdigest()
                source_name = letter.eml.name

                if apply_changes:
                    new_basename = os.path.basename(source_name)
                    letter.eml.save(
                        new_basename, ContentFile(source_bytes), save=False
                    )

                    if letter.eml.name == source_name:
                        raise CommandError(
                            f"Letter pk={letter.pk}: new file got the same "
                            "name as the original; refusing to continue."
                        )

                    with letter.eml.storage.open(letter.eml.name, "rb") as f:
                        new_hash = hashlib.sha256(f.read()).hexdigest()
                    if new_hash != source_hash:
                        raise CommandError(
                            f"Letter pk={letter.pk}: copy verification "
                            f"failed ({source_name!r} -> "
                            f"{letter.eml.name!r})"
                        )

                    logger.info(
                        "Letter pk=%s: copied eml %r -> %r",
                        letter.pk,
                        source_name,
                        letter.eml.name,
                    )
                else:
                    logger.info(
                        "Letter pk=%s: would copy eml %r to an independent "
                        "file",
                        letter.pk,
                        source_name,
                    )

        if apply_changes:
            letter.message = None
            if missing_eml:
                letter.save(update_fields=["message"])
            else:
                letter.save(update_fields=["eml", "message"])

        return missing_eml

    def _find_unexpected_references(self):
        """FK constraints pointing at django_mailbox tables from tables
        Django doesn't know about (e.g. stray backup tables left behind by
        manual schema work). MySQL enforces these even though the ORM's
        delete collector has no idea they exist, so they need to be
        surfaced up front instead of surfacing mid-delete as a raw
        IntegrityError.
        """
        target_tables = {
            Mailbox._meta.db_table,
            Message._meta.db_table,
            MessageAttachment._meta.db_table,
        }
        known_tables = {model._meta.db_table for model in apps.get_models()}

        placeholders = ", ".join(["%s"] * len(target_tables))
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT TABLE_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME "
                "FROM information_schema.KEY_COLUMN_USAGE "
                "WHERE REFERENCED_TABLE_SCHEMA = DATABASE() "
                f"AND REFERENCED_TABLE_NAME IN ({placeholders})",
                list(target_tables),
            )
            rows = cursor.fetchall()

        return [row for row in rows if row[0] not in known_tables]

    def _purge_mailbox_data(self, apply_changes):
        mailbox_count = Mailbox.objects.count()
        message_count = Message.objects.count()
        attachment_count = MessageAttachment.objects.count()
        logger.info(
            "django_mailbox data to purge: %s mailboxes, %s messages, "
            "%s attachments",
            mailbox_count,
            message_count,
            attachment_count,
        )

        unexpected = self._find_unexpected_references()
        if unexpected:
            details = "; ".join(
                f"{table}.{constraint} -> {referenced}"
                for table, constraint, referenced in unexpected
            )
            message = (
                "Found foreign key(s) into django_mailbox tables from "
                f"table(s) Django doesn't manage: {details}. These are "
                "likely leftover backup/scratch tables from manual schema "
                "work; left in place they will abort the delete with an "
                "IntegrityError partway through. Drop the constraint(s) "
                "or table(s) manually, then re-run."
            )
            if apply_changes:
                raise CommandError(message)
            logger.warning(message)

        if not apply_changes:
            logger.info("Dry-run: django_mailbox data was not deleted")
            return

        with transaction.atomic():
            MessageAttachment.objects.all().delete()
            Message.objects.all().delete()
            Mailbox.objects.all().delete()
        logger.info("django_mailbox data purged")
