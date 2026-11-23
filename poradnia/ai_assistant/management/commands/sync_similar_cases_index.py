from argparse import ArgumentTypeError, BooleanOptionalAction
from pprint import pformat

from django.core.management import BaseCommand, CommandError

from poradnia.ai_assistant.tasks import SYNC_MODES, sync_similar_cases_index_task


def _id_list(value):
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
        parser.add_argument(
            "--mode",
            choices=SYNC_MODES,
            default="incremental",
            help=(
                "initial: index eligible cases that were never indexed;"
                " incremental: re-sync cases changed since their last sync or"
                " in error, and remove ones no longer eligible;"
                " reconcile: compare indexed cases with n8n, drop orphans and"
                " re-index missing ones (default: %(default)s)."
            ),
        )
        parser.add_argument(
            "--pause-seconds",
            type=int,
            default=None,
            help=(
                "Delay between enqueued per-case syncs"
                " (default: SIMILAR_CASES_SYNC_PAUSE_SECONDS)."
            ),
        )
        # One of these is required, so an argument-less run can't sync the
        # whole index by mistake.
        selection = parser.add_mutually_exclusive_group(required=True)
        selection.add_argument(
            "--all",
            action="store_true",
            help="Sync every case selected by --mode (the only choice for reconcile).",
        )
        selection.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Sync at most this many cases (not allowed with reconcile).",
        )
        selection.add_argument(
            "--case-ids",
            type=_id_list,
            default=None,
            metavar="ID[,ID...]",
            help=(
                "Comma-separated case IDs to restrict the sync to; works even"
                " while SIMILAR_CASES_INDEX_ENABLED is off (not allowed with"
                " reconcile)."
            ),
        )
        parser.add_argument(
            "--scope-ids",
            type=_id_list,
            default=None,
            metavar="ID[,ID...]",
            help=(
                "Comma-separated advice scope IDs; restrict the sync to cases"
                " whose advice has one of these scopes (not allowed with"
                " reconcile)."
            ),
        )
        parser.add_argument(
            "--force-check",
            action="store_true",
            help=(
                "With --mode incremental: check every eligible or indexed case,"
                " not only those changed since their last sync."
            ),
        )
        parser.add_argument(
            "--force-reembed",
            action="store_true",
            help=(
                "With --mode initial: also re-index cases that are already"
                " indexed, discarding their stored index state."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action=BooleanOptionalAction,
            default=True,
            help=(
                "Only report what would be synced; enqueue nothing. On by"
                " default, pass --no-dry-run to actually sync."
            ),
        )
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Run in this process and print the counts instead of enqueuing.",
        )

    def handle(self, **options):
        if options["mode"] == "reconcile" and (
            not options["all"] or options["scope_ids"]
        ):
            raise CommandError(
                "--mode reconcile needs --all and can't be combined with"
                " --scope-ids: n8n deletes every indexed case missing from the list."
            )
        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN: only counting, nothing will be synced."
                    " Pass --no-dry-run to sync."
                )
            )
        kwargs = {
            "mode": options["mode"],
            "pause_seconds": options["pause_seconds"],
            "limit": options["limit"],
            "case_ids": options["case_ids"],
            "scope_ids": options["scope_ids"],
            "force_check": options["force_check"],
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
