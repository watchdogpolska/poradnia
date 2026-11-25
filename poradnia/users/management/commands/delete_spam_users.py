from datetime import timedelta

from django.core.management import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from poradnia.users.models import User


class Command(BaseCommand):
    help = (
        "Delete users matched by the admin 'Is SPAM user' = Yes filter "
        "(no login, no cases, no letters), oldest first. Staff, superusers, "
        "users referenced by advices and system accounts are never deleted."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            required=True,
            help="Maximum number of users to delete in this run.",
        )
        parser.add_argument(
            "--email-domain",
            help="Only users whose e-mail is in this domain (e.g. example.com).",
        )
        parser.add_argument(
            "--older-than-days",
            type=int,
            help="Only users who joined more than this many days ago.",
        )

    def get_queryset(self, email_domain=None, older_than_days=None):
        qs = User.objects.spam()
        if email_domain:
            qs = qs.filter(email__iendswith="@" + email_domain)
        if older_than_days is not None:
            cutoff = timezone.now() - timedelta(days=older_than_days)
            qs = qs.filter(date_joined__lt=cutoff)
        return qs

    def handle(self, **options):
        limit = options["limit"]
        if limit < 1:
            raise CommandError("--limit must be a positive integer.")
        older_than_days = options["older_than_days"]
        if older_than_days is not None and older_than_days < 0:
            raise CommandError("--older-than-days must not be negative.")
        email_domain = (options["email_domain"] or "").strip().lstrip("@").lower()

        qs = self.get_queryset(email_domain, older_than_days)
        matching_count = qs.count()
        pks = list(
            qs.order_by("date_joined", "pk").values_list("pk", flat=True)[:limit]
        )

        self.stdout.write(f"Spam users matching the criteria: {matching_count}")
        self.stdout.write(f"Users to be deleted (limit {limit}): {len(pks)}")
        if not pks:
            return

        answer = input(f"Delete {len(pks)} users (y/n)? ")
        if answer.strip().lower() != "y":
            self.stdout.write("Aborted, nothing deleted.")
            return

        with transaction.atomic():
            total, per_model = User.objects.filter(pk__in=pks).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {total} objects in total:"))
        for label, count in sorted(per_model.items()):
            self.stdout.write(f"  {label}: {count}")
