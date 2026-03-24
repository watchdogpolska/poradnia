import logging
import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class FindOrphanedFilesBaseCommand(BaseCommand):
    """
    Base management command for finding orphaned files under a MEDIA_ROOT
    subdirectory, optionally deleting them, and removing empty directories.

    Subclasses must define:
    - queryset_model
    - queryset_field_name
    - base_subdir
    - path_label
    - file_label_plural
    - object_label_singular
    """

    queryset_model = None
    queryset_field_name = None
    base_subdir = None
    path_label = "Base path"
    file_label_plural = "files"
    object_label_singular = "object"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            help=f"Actually delete orphaned {self.file_label_plural} "
            "and empty directories",
            action="store_true",
        )

    def handle(self, *args, **options):
        delete_mode = options["delete"]
        base_path = os.path.join(settings.MEDIA_ROOT, self.base_subdir)

        self._validate_configuration()
        self._log_start(base_path=base_path, options=options)

        if not self._validate_base_path(base_path):
            return

        existing_paths = self._load_existing_paths()

        orphan_files, orphan_files_size, total_files_checked, total_dirs_seen = (
            self._scan_orphan_files(
                base_path=base_path,
                existing_paths=existing_paths,
            )
        )

        self._log_scan_summary(
            total_dirs_seen=total_dirs_seen,
            total_files_checked=total_files_checked,
            orphan_files=orphan_files,
            orphan_files_size=orphan_files_size,
        )

        if delete_mode:
            self._delete_files(orphan_files)
        else:
            logger.info(
                "Dry-run: orphaned %s were not deleted",
                self.file_label_plural,
            )

        empty_dirs = self._find_empty_dirs(base_path)
        logger.info("Empty directories found: %s", len(empty_dirs))

        if delete_mode:
            self._delete_dirs(empty_dirs)
            self._log_delete_summary(
                total_dirs_seen=total_dirs_seen,
                total_files_checked=total_files_checked,
                orphan_files=orphan_files,
                orphan_files_size=orphan_files_size,
                empty_dirs=empty_dirs,
            )
        else:
            logger.info("Dry-run: empty directories were not deleted")

        self._log_end()

    def _validate_configuration(self):
        required_attrs = [
            "queryset_model",
            "queryset_field_name",
            "base_subdir",
        ]

        missing = [attr for attr in required_attrs if getattr(self, attr, None) is None]
        if missing:
            raise NotImplementedError(
                "Missing required class attributes: %s" % ", ".join(missing)
            )

    def _log_start(self, *, base_path, options):
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Started: %s", start_time)
        logger.info("Options: %s", options)
        logger.info("%s: %s", self.path_label, base_path)

    def _log_end(self):
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Completed: %s", end_time)

    def _validate_base_path(self, base_path):
        if not os.path.exists(base_path):
            logger.warning("Base path does not exist: %s", base_path)
            return False

        if not os.path.isdir(base_path):
            logger.error("Base path is not a directory: %s", base_path)
            return False

        return True

    def _load_existing_paths(self):
        logger.info(
            "Loading %s paths from database...",
            self.file_label_plural,
        )
        existing_paths = set(
            self.queryset_model.objects.values_list(
                self.queryset_field_name,
                flat=True,
            )
        )
        logger.info(
            "Loaded %s %s paths from database",
            len(existing_paths),
            self.file_label_plural,
        )
        return existing_paths

    def _scan_orphan_files(self, *, base_path, existing_paths):
        orphan_files = []
        orphan_files_size = 0
        total_files_checked = 0
        total_dirs_seen = 0

        logger.info(
            "Scanning filesystem for orphaned %s...",
            self.file_label_plural,
        )

        for root, _, files in os.walk(base_path):
            total_dirs_seen += 1

            for filename in files:
                total_files_checked += 1
                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, settings.MEDIA_ROOT)

                if rel_path in existing_paths:
                    logger.debug(
                        "%s: %s exists for %s",
                        total_files_checked,
                        self.object_label_singular,
                        abs_path,
                    )
                    continue

                file_size = self._get_file_size(
                    abs_path=abs_path,
                    file_number=total_files_checked,
                )
                if file_size is None:
                    continue

                orphan_files_size += file_size
                orphan_files.append(abs_path)
                logger.warning(
                    "%s: %s missing for %s",
                    total_files_checked,
                    self.object_label_singular,
                    abs_path,
                )

        logger.info("Filesystem scan completed")
        return (
            orphan_files,
            orphan_files_size,
            total_files_checked,
            total_dirs_seen,
        )

    def _get_file_size(self, *, abs_path, file_number):
        try:
            return os.stat(abs_path).st_size
        except FileNotFoundError:
            logger.warning(
                "%s: file disappeared during scan: %s",
                file_number,
                abs_path,
            )
        except OSError as exc:
            logger.error(
                "%s: failed to stat file %s: %s",
                file_number,
                abs_path,
                exc,
            )
        return None

    def _delete_files(self, orphan_files):
        logger.info("Deleting orphaned %s...", self.file_label_plural)
        for abs_path in orphan_files:
            try:
                os.remove(abs_path)
                logger.info("Deleted file: %s", abs_path)
            except FileNotFoundError:
                logger.warning("File already missing: %s", abs_path)
            except OSError as exc:
                logger.error("Failed to delete file %s: %s", abs_path, exc)

    def _find_empty_dirs(self, base_path):
        logger.info("Scanning for empty directories...")
        empty_dirs = []

        for root, _, _ in os.walk(base_path, topdown=False):
            if root == base_path:
                continue

            try:
                if not os.listdir(root):
                    empty_dirs.append(root)
            except FileNotFoundError:
                continue
            except OSError as exc:
                logger.error("Failed to inspect dir %s: %s", root, exc)

        return empty_dirs

    def _delete_dirs(self, empty_dirs):
        logger.info("Deleting empty directories...")
        for dir_path in empty_dirs:
            try:
                os.rmdir(dir_path)
                logger.info("Deleted empty dir: %s", dir_path)
            except FileNotFoundError:
                logger.warning("Directory already missing: %s", dir_path)
            except OSError as exc:
                logger.error("Failed to delete dir %s: %s", dir_path, exc)

    def _log_scan_summary(
        self,
        *,
        total_dirs_seen,
        total_files_checked,
        orphan_files,
        orphan_files_size,
    ):
        logger.info("Directories seen: %s", total_dirs_seen)
        logger.info("Files checked: %s", total_files_checked)
        logger.info(
            "Orphaned %s: %s files, %.2f MB",
            self.file_label_plural,
            len(orphan_files),
            orphan_files_size / (1024 * 1024),
        )

    def _log_delete_summary(
        self,
        *,
        total_dirs_seen,
        total_files_checked,
        orphan_files,
        orphan_files_size,
        empty_dirs,
    ):
        logger.info("Filesystem scan completed")
        logger.info("Directories seen: %s", total_dirs_seen)
        logger.info("Files checked: %s", total_files_checked)
        logger.info(
            "Deleted orphaned %s: %s files, %.2f MB",
            self.file_label_plural,
            len(orphan_files),
            orphan_files_size / (1024 * 1024),
        )
        logger.info("Deleted empty directories found: %s", len(empty_dirs))
