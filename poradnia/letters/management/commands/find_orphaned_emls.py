import logging
import os
from datetime import datetime
from glob import glob

from django.conf import settings
from django.core.management.base import BaseCommand

from poradnia.letters.models import Letter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Find orphaned eml files - not linked to any letter"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            help="Confirm deletion of orphaned eml",
            action="store_true",
        )

    def handle(self, *args, **options):
        orphans = []
        orphans_size = 0

        base_path = os.path.join(settings.MEDIA_ROOT, "messages")
        msg_path = f"{base_path}/**"

        msg_files = glob(msg_path, recursive=True)
        msg_files.sort()

        tot_emls = len(msg_files)
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"total message files to check: {tot_emls}")
        logger.info(f"Options: {options}")
        logger.info(f"Started: {start_time}")

        # IMPORTANT: materialize queryset once (avoid repeated DB hits)
        letter_emls = set(Letter.objects.values_list("eml", flat=True))

        for count, file in enumerate(msg_files):
            if os.path.isdir(file):
                logger.info(f"{count} of {tot_emls}: {file} is directory - skipping")
                continue

            rel_path = file.replace(settings.MEDIA_ROOT + "/", "")

            if rel_path in letter_emls:
                logger.info(f"{count} of {tot_emls}: letter exists for {file}")
            else:
                file_stats = os.stat(file)
                orphans_size += file_stats.st_size
                orphans.append(file)
                logger.warning(f"{count} of {tot_emls}: letter missing for {file}")

        logger.info(
            "Orphaned emls: {:,} files of {:,.2f}MB".format(
                len(orphans), orphans_size / (1024 * 1024)
            )
        )

        if options["delete"]:
            logger.info("Deleting orphaned eml files...")

            for eml in orphans:
                try:
                    os.remove(eml)
                    logger.info(f"Deleted {eml}")
                except Exception as e:
                    logger.error(f"Failed to delete {eml}: {e}")

            # ✅ NEW: remove empty directories (bottom-up)
            logger.info("Cleaning up empty directories...")

            removed_dirs = 0

            for root, dirs, files in os.walk(base_path, topdown=False):
                try:
                    if not os.listdir(root):
                        os.rmdir(root)
                        removed_dirs += 1
                        logger.info(f"Removed empty directory: {root}")
                except Exception as e:
                    logger.error(f"Failed to remove directory {root}: {e}")

            logger.info(f"Removed {removed_dirs} empty directories")

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Completed: {end_time}")
