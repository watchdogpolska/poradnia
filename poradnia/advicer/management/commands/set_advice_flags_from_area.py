from django.core.management.base import BaseCommand

from poradnia.advicer.models import Advice

ISSUE_FLAG_MAP = {
    "ciekawa sprawa": "interesting_case",
    "do poradnika": "for_knowledge_base",
}


class Command(BaseCommand):
    help = (
        "Set Advice.interesting_case / Advice.for_knowledge_base based on Issue names."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        label = "[DRY RUN] " if dry_run else ""

        for issue_name, field_name in ISSUE_FLAG_MAP.items():
            qs = Advice.objects.filter(issues__name=issue_name).exclude(
                **{field_name: True}
            )
            count = qs.count()
            for advice in qs.select_related():
                self.stdout.write(
                    f"  {label}Advice pk={advice.pk}: {field_name} = True"
                )
            if not dry_run:
                qs.update(**{field_name: True})
            self.stdout.write(
                self.style.SUCCESS(
                    f"{label}issue='{issue_name}' → "
                    f"{field_name}: updated {count} advice(s)"
                )
            )
