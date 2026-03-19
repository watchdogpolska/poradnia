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
            "--delete", help="Confirm deletion of orphaned eml", action="store_true"
        )

    def handle(self, *args, **options):
        orphans = []
        orphans_size = 0
        msg_path = f"{settings.MEDIA_ROOT}/messages/**"
        msg_files = glob(msg_path, recursive=True)
        msg_files.sort()
        tot_emls = len(msg_files)
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"total message files to check: {tot_emls}")
        logger.info(f"Options: {options}")
        logger.info(f"Started: {start_time}")
        letter_emls = Letter.objects.values_list("eml", flat=True)
        for count, file in enumerate(msg_files):
            if os.path.isdir(file):
                logger.info(f"{count} of {tot_emls}: {file} is directory - skipping")
                continue
            if file.replace(settings.MEDIA_ROOT + "/", "") in letter_emls:
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
                os.remove(eml)
                logger.info(f"Deleted {eml}")
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Completed: {end_time}")
