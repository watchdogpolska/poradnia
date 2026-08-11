import hashlib
import logging
import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
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
        "Letter.message. Once no Letter references django_mailbox any "
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
        for letter in letters:
            try:
                self._detach_letter(letter, apply_changes)
            except Exception:
                failed += 1
                logger.exception("Failed to detach letter pk=%s", letter.pk)

        detached = total - failed
        logger.info("Detached: %s, failed: %s", detached, failed)

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

        if shares_file:
            with letter.eml.storage.open(letter.eml.name, "rb") as f:
                source_bytes = f.read()
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
                        f"Letter pk={letter.pk}: copy verification failed "
                        f"({source_name!r} -> {letter.eml.name!r})"
                    )

                logger.info(
                    "Letter pk=%s: copied eml %r -> %r",
                    letter.pk,
                    source_name,
                    letter.eml.name,
                )
            else:
                logger.info(
                    "Letter pk=%s: would copy eml %r to an independent file",
                    letter.pk,
                    source_name,
                )

        if apply_changes:
            letter.message = None
            letter.save(update_fields=["eml", "message"])

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

        if not apply_changes:
            logger.info("Dry-run: django_mailbox data was not deleted")
            return

        MessageAttachment.objects.all().delete()
        Message.objects.all().delete()
        Mailbox.objects.all().delete()
        logger.info("django_mailbox data purged")
