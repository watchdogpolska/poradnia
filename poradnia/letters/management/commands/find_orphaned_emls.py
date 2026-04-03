from poradnia.letters.management.commands._find_orphaned_files_base import (
    FindOrphanedFilesBaseCommand,
)
from poradnia.letters.models import Letter


class Command(FindOrphanedFilesBaseCommand):
    help = (
        "Find orphaned message files under MEDIA_ROOT/messages, "
        "optionally delete them, and remove empty directories."
    )

    queryset_model = Letter
    queryset_field_name = "eml"
    base_subdir = "messages"
    path_label = "Base path"
    file_label_plural = "message files"
    object_label_singular = "letter"
