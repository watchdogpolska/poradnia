import glob
import os

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand

from poradnia.advicer.models import Area, InstitutionKind, Issue, PersonKind

MODEL_MAP = {
    "tag_helper-advicer_area": Area,
    "tag_helper-advicer_institutionkind": InstitutionKind,
    "tag_helper-advicer_issue": Issue,
    "tag_helper-advicer_personkind": PersonKind,
}


class Command(BaseCommand):
    help = "Import tag_helper content from YAML files into advicer category models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without writing to the database.",
        )
        parser.add_argument(
            "--dir",
            default=None,
            help=(
                "Directory to scan for tag_helper-*.yaml files. "
                "Defaults to tag_helper/ under MEDIA_ROOT."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        search_dir = os.path.abspath(
            options["dir"] or os.path.join(settings.MEDIA_ROOT, "tag_helper")
        )
        pattern = os.path.join(search_dir, "tag_helper-*.yaml")
        files = sorted(glob.glob(pattern))

        if not files:
            self.stderr.write(f"No YAML files found matching: {pattern}")
            return

        for path in files:
            stem = os.path.splitext(os.path.basename(path))[0]
            model = MODEL_MAP.get(stem)
            if model is None:
                self.stderr.write(self.style.WARNING(f"Skipping unknown file: {path}"))
                continue
            self._process_file(path, model, dry_run)

    def _process_file(self, path, model, dry_run):
        with open(path, encoding="utf-8") as f:
            entries = yaml.safe_load(f)

        if not entries:
            self.stderr.write(self.style.WARNING(f"Empty file: {path}"))
            return

        created = updated = skipped = 0

        for entry in entries:
            tag_helper_value = entry.get("tag_helper") or entry.get("description")
            name_value = entry.get("name")
            entry_id = entry.get("id")

            if entry_id is not None:
                result = self._process_entry_by_id(
                    model, entry_id, name_value, tag_helper_value, dry_run
                )
            else:
                result = self._process_entry_by_name(
                    model, name_value, tag_helper_value, dry_run
                )

            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1
            else:
                skipped += 1

        label = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{label}{model.__name__}: "
                f"created={created}, updated={updated}, skipped={skipped}"
            )
        )

    def _process_entry_by_id(
        self, model, entry_id, name_value, tag_helper_value, dry_run
    ):
        try:
            obj = model.objects.get(pk=entry_id)
        except model.DoesNotExist:
            self.stderr.write(
                self.style.WARNING(
                    f"{model.__name__} id={entry_id} not found, skipping."
                )
            )
            return "skipped"
        changed = self._apply_changes(obj, name_value, tag_helper_value)
        if changed:
            if not dry_run:
                obj.save(update_fields=["name", "tag_helper"])
            self._log_change("updated", model, obj.pk, name_value, dry_run)
            return "updated"
        return "skipped"

    def _process_entry_by_name(self, model, name_value, tag_helper_value, dry_run):
        obj, was_created = model.objects.get_or_create(
            name=name_value,
            defaults={"tag_helper": tag_helper_value, "active": True},
        )
        if was_created:
            if dry_run:
                obj.delete()
            self._log_change("created", model, obj.pk, name_value, dry_run)
            return "created"
        changed = self._apply_changes(obj, name_value, tag_helper_value)
        if changed:
            if not dry_run:
                obj.save(update_fields=["name", "tag_helper"])
            self._log_change("updated", model, obj.pk, name_value, dry_run)
            return "updated"
        return "skipped"

    def _apply_changes(self, obj, name_value, tag_helper_value):
        changed = False
        if name_value and obj.name != name_value:
            obj.name = name_value
            changed = True
        if tag_helper_value and obj.tag_helper != tag_helper_value:
            obj.tag_helper = tag_helper_value
            changed = True
        return changed

    def _log_change(self, action, model, pk, name, dry_run):
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(f"  {prefix}{model.__name__} pk={pk} ({name}): {action}")
