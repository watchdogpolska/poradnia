from collections import Counter, defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from poradnia.advicer.models import Advice, Scope

FLAG_FIELDS = Scope.FLAG_FIELDS


def flags_label(flags):
    names = [name for name, value in zip(FLAG_FIELDS, flags) if value]
    return ", ".join(names) or "no flags set"


class Command(BaseCommand):
    help = (
        "Check that active Scope flag combinations are unique, then assign "
        "Advice.scope from the flags of the advice's issues, after confirmation."
    )

    def handle(self, *args, **options):
        scope_by_flags = self._get_scope_by_flags()
        self.stdout.write(
            f"Active scopes have unique flags: {len(scope_by_flags)} scope(s)."
        )

        advice_flags = self._get_unscoped_advice_flags()
        pks_by_scope, unmatched = self._match_scopes(advice_flags, scope_by_flags)
        self._report(advice_flags, pks_by_scope, unmatched)

        assignable = sum(len(pks) for pks in pks_by_scope.values())
        if not assignable:
            self.stdout.write("Nothing to assign.")
            return

        answer = input(f"Assign scopes to {assignable} advice(s)? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            self.stdout.write("Aborted, no changes made.")
            return

        updated = self._assign(pks_by_scope)
        self.stdout.write(self.style.SUCCESS(f"Assigned {updated} advice(s)."))

    def _get_scope_by_flags(self):
        """Map each flag combination to its active scope, refusing duplicates."""
        scopes_by_flags = defaultdict(list)
        for scope in Scope.objects.filter(active=True).order_by("name"):
            flags = tuple(getattr(scope, flag) for flag in FLAG_FIELDS)
            scopes_by_flags[flags].append(scope)

        duplicates = [
            f"  {flags_label(flags)}: {', '.join(scope.name for scope in scopes)}"
            for flags, scopes in scopes_by_flags.items()
            if len(scopes) > 1
        ]
        if duplicates:
            raise CommandError(
                "Active scopes share the same flags, so a scope cannot be "
                "selected deterministically:\n" + "\n".join(duplicates)
            )
        return {flags: scopes[0] for flags, scopes in scopes_by_flags.items()}

    def _get_unscoped_advice_flags(self):
        """Map each advice without a scope to its issues' flag combinations."""
        rows = (
            Advice.objects.filter(scope__isnull=True)
            .order_by()
            .values_list("pk", *(f"issues__{flag}" for flag in FLAG_FIELDS))
        )
        advice_flags = defaultdict(set)
        for pk, *flags in rows:
            # An advice without issues comes back as a single all-NULL row.
            if flags[0] is None:
                advice_flags[pk]
            else:
                advice_flags[pk].add(tuple(flags))
        return advice_flags

    def _match_scopes(self, advice_flags, scope_by_flags):
        pks_by_scope = defaultdict(list)
        unmatched = Counter()
        for pk, combinations in advice_flags.items():
            if len(combinations) != 1:
                continue
            (flags,) = combinations
            if flags in scope_by_flags:
                pks_by_scope[scope_by_flags[flags]].append(pk)
            else:
                unmatched[flags] += 1
        return pks_by_scope, unmatched

    def _report(self, advice_flags, pks_by_scope, unmatched):
        combination_counts = Counter(len(flags) for flags in advice_flags.values())
        mixed = sum(n for size, n in combination_counts.items() if size > 1)
        no_issues_no_case = Advice.objects.filter(
            scope__isnull=True, issues__isnull=True, case__isnull=True
        ).count()

        self.stdout.write(f"Advices without a scope: {len(advice_flags)}")
        self.stdout.write(f"  no issues: {combination_counts[0]}")
        self.stdout.write(f"    no case: {no_issues_no_case}")
        self.stdout.write(f"  issues with mixed flags: {mixed}")
        self.stdout.write(f"  no active scope for flags: {sum(unmatched.values())}")
        for flags, count in unmatched.most_common():
            self.stdout.write(f"    {flags_label(flags)}: {count}")
        assignable = sum(len(pks) for pks in pks_by_scope.values())
        self.stdout.write(f"  assignable: {assignable}")
        for scope, pks in sorted(pks_by_scope.items(), key=lambda item: item[0].name):
            self.stdout.write(f"    {scope.name}: {len(pks)}")

    def _assign(self, pks_by_scope):
        updated = 0
        with transaction.atomic():
            for scope, pks in pks_by_scope.items():
                # The scope__isnull filter keeps a scope set since the report.
                updated += Advice.objects.filter(pk__in=pks, scope__isnull=True).update(
                    scope=scope
                )
        return updated
