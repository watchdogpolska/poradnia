import logging
import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from poradnia.letters.models import Letter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Find orphaned .eml files under MEDIA_ROOT/messages, "
        "optionally delete them, and remove empty directories."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            help="Actually delete orphaned .eml files and empty directories",
            action="store_true",
        )

    def handle(self, *args, **options):
        delete_mode = options["delete"]
        base_path = os.path.join(settings.MEDIA_ROOT, "messages")

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Started: %s", start_time)
        logger.info("Options: %s", options)
        logger.info("Base path: %s", base_path)

        if not os.path.exists(base_path):
            logger.warning("Base path does not exist: %s", base_path)
            return

        if not os.path.isdir(base_path):
            logger.error("Base path is not a directory: %s", base_path)
            return

        logger.info("Loading .eml paths from database...")
        existing_paths = set(Letter.objects.values_list("eml", flat=True))
        logger.info("Loaded %s .eml paths from database", len(existing_paths))

        orphan_files = []
        orphan_files_size = 0
        total_files_checked = 0
        total_dirs_seen = 0

        logger.info("Scanning filesystem for orphaned .eml files...")

        for root, dirs, files in os.walk(base_path):
            total_dirs_seen += 1

            for filename in files:
                total_files_checked += 1
                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, settings.MEDIA_ROOT)

                if rel_path in existing_paths:
                    logger.debug(
                        "%s: letter exists for %s",
                        total_files_checked,
                        abs_path,
                    )
                    continue

                try:
                    file_stats = os.stat(abs_path)
                except FileNotFoundError:
                    logger.warning(
                        "%s: file disappeared during scan: %s",
                        total_files_checked,
                        abs_path,
                    )
                    continue
                except OSError as exc:
                    logger.error(
                        "%s: failed to stat file %s: %s",
                        total_files_checked,
                        abs_path,
                        exc,
                    )
                    continue

                orphan_files_size += file_stats.st_size
                orphan_files.append(abs_path)
                logger.warning(
                    "%s: letter missing for %s",
                    total_files_checked,
                    abs_path,
                )

        logger.info("Filesystem scan completed")
        logger.info("Directories seen: %s", total_dirs_seen)
        logger.info("Files checked: %s", total_files_checked)
        logger.info(
            "Orphaned .eml files: %s files, %.2f MB",
            len(orphan_files),
            orphan_files_size / (1024 * 1024),
        )

        if delete_mode:
            logger.info("Deleting orphaned .eml files...")
            for abs_path in orphan_files:
                try:
                    os.remove(abs_path)
                    logger.info("Deleted file: %s", abs_path)
                except FileNotFoundError:
                    logger.warning("File already missing: %s", abs_path)
                except OSError as exc:
                    logger.error("Failed to delete file %s: %s", abs_path, exc)
        else:
            logger.info("Dry-run: orphaned .eml files were not deleted")
            for abs_path in orphan_files:
                logger.info("Dry-run: would delete file: %s", abs_path)

        logger.info("Scanning for empty directories...")
        empty_dirs = []

        for root, dirs, files in os.walk(base_path, topdown=False):
            if root == base_path:
                continue

            if not dirs and not files:
                empty_dirs.append(root)
                logger.warning("Empty directory found: %s", root)

        logger.info("Empty directories found: %s", len(empty_dirs))

        if delete_mode:
            logger.info("Deleting empty directories...")
            for dir_path in empty_dirs:
                try:
                    os.rmdir(dir_path)
                    logger.info("Deleted empty dir: %s", dir_path)
                except FileNotFoundError:
                    logger.warning("Directory already missing: %s", dir_path)
                except OSError as exc:
                    logger.error("Failed to delete dir %s: %s", dir_path, exc)
        else:
            logger.info("Dry-run: empty directories were not deleted")
            for dir_path in empty_dirs:
                logger.info("Dry-run: would delete empty dir: %s", dir_path)

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Completed: %s", end_time)
