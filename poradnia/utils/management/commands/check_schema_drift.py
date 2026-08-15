from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = "Find DB tables/columns not present in Django models (schema drift)."

    def add_arguments(self, parser):
        parser.add_argument("--database", default="default")
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit with a non-zero status if any drift is found (for CI/cron).",
        )

    def handle(self, *args, **opts):
        conn = connections[opts["database"]]

        # --- what the models expect ---
        model_tables = set()
        model_columns = set()  # (table, column)
        for model in apps.get_models(include_auto_created=True):
            table = model._meta.db_table
            model_tables.add(table)
            for field in model._meta.local_concrete_fields:
                model_columns.add((table, field.column))

        # --- what actually exists in the DB ---
        with conn.cursor() as cursor:
            db_tables = set(conn.introspection.table_names(cursor))
            db_columns = set()
            for table in db_tables:
                try:
                    desc = conn.introspection.get_table_description(cursor, table)
                except Exception:
                    continue  # views / permission edge cases
                for col in desc:
                    db_columns.add((table, col.name))

        # framework tables Django manages without a model
        ignore_tables = {"django_migrations"}

        shared = db_tables & model_tables

        leftover_tables = (db_tables - model_tables) - ignore_tables
        leftover_columns = {
            (t, c) for (t, c) in (db_columns - model_columns) if t in shared
        }
        # reverse direction = unapplied/missing migration
        missing_tables = model_tables - db_tables
        missing_columns = {
            (t, c) for (t, c) in (model_columns - db_columns) if t in shared
        }

        self._report("Leftover tables (in DB, no model)", sorted(leftover_tables))
        self._report(
            "Leftover columns (in DB, not in model)",
            sorted(f"{t}.{c}" for t, c in leftover_columns),
        )
        self._report("Missing tables (model, not in DB)", sorted(missing_tables))
        self._report(
            "Missing columns (model, not in DB)",
            sorted(f"{t}.{c}" for t, c in missing_columns),
        )

        drift_found = any(
            [leftover_tables, leftover_columns, missing_tables, missing_columns]
        )
        if opts["strict"] and drift_found:
            raise CommandError("Schema drift detected (see report above).")

    def _report(self, title, items):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{title}: {len(items)}"))
        for item in items:
            self.stdout.write(f"  {item}")
