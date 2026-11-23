from argparse import ArgumentTypeError
from pprint import pformat

from django.core.management import BaseCommand, CommandError

from poradnia.ai_assistant.tasks import SYNC_MODES, sync_similar_cases_index_task


def _case_ids(value):
    try:
        return [int(pk) for pk in value.split(",") if pk.strip()]
    except ValueError:
        raise ArgumentTypeError(f"must be comma-separated integers: {value!r}")


class Command(BaseCommand):
    help = (
        "Push eligible closed cases to the n8n similar-cases index "
        "(initial load, incremental re-sync or reconcile)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--mode", choices=SYNC_MODES, default="incremental")
        parser.add_argument("--pause-seconds", type=int, default=None)
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--case-ids", type=_case_ids, default=None)
        parser.add_argument("--force-reembed", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Run in this process and print the counts instead of enqueuing.",
        )

    def handle(self, **options):
        if options["mode"] == "reconcile" and (options["case_ids"] or options["limit"]):
            raise CommandError(
                "--mode reconcile can't be combined with --case-ids or --limit:"
                " n8n deletes every indexed case missing from the list."
            )
        kwargs = {
            "mode": options["mode"],
            "pause_seconds": options["pause_seconds"],
            "limit": options["limit"],
            "case_ids": options["case_ids"],
            "force_reembed": options["force_reembed"],
            "dry_run": options["dry_run"],
        }
        if options["sync"]:
            result = sync_similar_cases_index_task.apply(kwargs=kwargs).get()
            self.stdout.write(
                " ".join(f"{key}={value}" for key, value in result.items())
            )
        else:
            task = sync_similar_cases_index_task.delay(**kwargs)
            self.stdout.write(f"Enqueued sync_similar_cases_index_task: {task.id}")
        self.stdout.write(f"kwargs:\n{pformat(kwargs)}")
