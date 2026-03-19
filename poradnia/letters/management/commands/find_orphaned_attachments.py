from poradnia.letters.management.commands._find_orphaned_files_base import (
    FindOrphanedFilesBaseCommand,
)
from poradnia.letters.models import Attachment


class Command(FindOrphanedFilesBaseCommand):
    help = (
        "Find orphaned attachment files under MEDIA_ROOT/letters, "
        "optionally delete them, and remove empty directories."
    )

    queryset_model = Attachment
    queryset_field_name = "attachment"
    base_subdir = "letters"
    path_label = "Base path"
    file_label_plural = "attachment files"
    object_label_singular = "attachment"
