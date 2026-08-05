from collections import defaultdict

from django.db.models import Count, Q
from django.db.models.functions import ExtractYear, TruncMonth
from django.utils.translation import gettext_lazy as _

from poradnia.advicer.models import Advice, Area, InstitutionKind, Issue, PersonKind
from poradnia.cases.models import Case
from poradnia.judgements.models import CourtCase, CourtSession
from poradnia.letters.models import Letter

TOTAL_LABEL = _("TOTAL")
ANY_TOTAL_LABEL = _("ANY / TOTAL")
NONE_LABEL = _("None")

CASE_LETTER_BUCKETS = (
    ("cases_le_5", _("cases <= 5"), 0, 5),
    ("cases_6_10", _("cases 6-10"), 6, 10),
    ("cases_11_20", _("cases 11-20"), 11, 20),
    ("cases_21_50", _("cases 21-50"), 21, 50),
    ("cases_50_plus", _("cases > 50"), 51, None),
)

CASE_LETTER_COUNT_BUCKETS = (
    ("b_le5", _("case letters count <=5"), 0, 5),
    ("b_6_10", _("case letters count 6-10"), 6, 10),
    ("b_11_20", _("case letters count 11-20"), 11, 20),
    ("b_21_50", _("case letters count 21-50"), 21, 50),
    ("b_51_100", _("case letters count 51-100"), 51, 100),
    ("b_100p", _("case letters count 100+"), 101, None),
)


def _bucket_filter(field, low, high):
    lookup = {f"{field}__gte": low}
    if high is not None:
        lookup[f"{field}__lte"] = high
    return Q(**lookup)


def _in_bucket(value, low, high):
    return value >= low and (high is None or value <= high)


def _month_columns():
    return [{"key": "month", "label": _("Month")}]


def users_report(year):
    """Monthly count of clients who opened new cases, bucketed by how many
    cases each client opened that month, plus a TOTAL row over all
    (client, month) groups (matches the source SQL's WITH ROLLUP semantics,
    i.e. it is not a distinct-client-per-year count).
    """
    columns = (
        _month_columns()
        + [
            {"key": "users_with_new_case", "label": _("users with new case")},
        ]
        + [{"key": key, "label": label} for key, label, _lo, _hi in CASE_LETTER_BUCKETS]
    )

    grouped = (
        Case.objects.filter(created_on__year=year, client_id__isnull=False)
        .annotate(month=TruncMonth("created_on"))
        .values("client_id", "month")
        .annotate(cnt=Count("id"))
    )

    by_month = defaultdict(list)
    for entry in grouped:
        by_month[entry["month"].strftime("%Y-%m")].append(entry["cnt"])

    def build_row(month_label, counts):
        row = {"month": month_label, "users_with_new_case": len(counts)}
        for key, _label, low, high in CASE_LETTER_BUCKETS:
            row[key] = sum(1 for cnt in counts if _in_bucket(cnt, low, high))
        return row

    rows = [
        build_row(month_label, counts)
        for month_label, counts in sorted(by_month.items())
    ]
    all_counts = [cnt for counts in by_month.values() for cnt in counts]
    total_row = build_row(str(TOTAL_LABEL), all_counts)
    total_row["pinned"] = True
    rows.append(total_row)

    return {"title": _("Users report"), "columns": columns, "rows": rows}


def cases_report(year):
    """Monthly count of cases created, bucketed by each case's (denormalized)
    letter_count, plus a TOTAL row.
    """
    columns = (
        _month_columns()
        + [{"key": "cases_created", "label": _("cases created")}]
        + [
            {"key": key, "label": label}
            for key, label, _lo, _hi in CASE_LETTER_COUNT_BUCKETS
        ]
    )

    annotations = {"cases_created": Count("id")}
    for key, _label, low, high in CASE_LETTER_COUNT_BUCKETS:
        annotations[key] = Count("id", filter=_bucket_filter("letter_count", low, high))

    grouped = (
        Case.objects.filter(created_on__year=year)
        .annotate(month=TruncMonth("created_on"))
        .values("month")
        .annotate(**annotations)
        .order_by("month")
    )

    rows = []
    totals = defaultdict(int)
    for entry in grouped:
        row = {"month": entry["month"].strftime("%Y-%m")}
        for key in annotations:
            row[key] = entry[key]
            totals[key] += entry[key]
        rows.append(row)

    total_row = {"month": str(TOTAL_LABEL), **totals, "pinned": True}
    rows.append(total_row)

    return {"title": _("Cases report"), "columns": columns, "rows": rows}


def staff_letters_report(year):
    """Monthly count of staff-authored letters and their attachments."""
    columns = _month_columns() + [
        {"key": "letters_by_staff", "label": _("letters by staff")},
        {"key": "attachments_by_staff", "label": _("attachments by staff")},
    ]

    grouped = (
        Letter.objects.filter(created_by_is_staff=True, created_on__year=year)
        .annotate(month=TruncMonth("created_on"))
        .values("month")
        .annotate(
            letters_by_staff=Count("id", distinct=True),
            attachments_by_staff=Count("attachment"),
        )
        .order_by("month")
    )

    rows = []
    total_letters = 0
    total_attachments = 0
    for entry in grouped:
        rows.append(
            {
                "month": entry["month"].strftime("%Y-%m"),
                "letters_by_staff": entry["letters_by_staff"],
                "attachments_by_staff": entry["attachments_by_staff"],
            }
        )
        total_letters += entry["letters_by_staff"]
        total_attachments += entry["attachments_by_staff"]

    rows.append(
        {
            "month": str(TOTAL_LABEL),
            "letters_by_staff": total_letters,
            "attachments_by_staff": total_attachments,
            "pinned": True,
        }
    )

    return {"title": _("Staff letters report"), "columns": columns, "rows": rows}


def _m2m_case_breakdown(year, m2m_field, related_model, id_column, name_column, title):
    total_cases = Case.objects.filter(created_on__year=year).count()

    pairs = (
        Advice.objects.filter(case__created_on__year=year, case__isnull=False)
        .values_list("case_id", f"{m2m_field}__id")
        .distinct()
    )

    cases_by_related = defaultdict(set)
    any_cases = set()
    for case_id, related_id in pairs:
        if related_id is None:
            continue
        cases_by_related[related_id].add(case_id)
        any_cases.add(case_id)

    names = dict(
        related_model.objects.filter(id__in=cases_by_related.keys()).values_list(
            "id", "name"
        )
    )

    columns = [
        {"key": id_column, "label": _("id")},
        {"key": name_column, "label": _("name")},
        {"key": "cases_assigned", "label": _("cases assigned")},
        {"key": "cases_missing", "label": _("cases missing")},
    ]

    rows = []
    for related_id in sorted(cases_by_related):
        cases_assigned = len(cases_by_related[related_id])
        rows.append(
            {
                id_column: related_id,
                name_column: names.get(related_id, ""),
                "cases_assigned": cases_assigned,
                "cases_missing": total_cases - cases_assigned,
            }
        )

    any_assigned = len(any_cases)
    rows.append(
        {
            id_column: "",
            name_column: str(ANY_TOTAL_LABEL),
            "cases_assigned": any_assigned,
            "cases_missing": total_cases - any_assigned,
            "pinned": True,
        }
    )

    return {"title": title, "columns": columns, "rows": rows}


def _fk_case_breakdown(year, fk_field, related_model, id_column, name_column, title):
    total_cases = Case.objects.filter(created_on__year=year).count()

    grouped = (
        Advice.objects.filter(
            case__created_on__year=year,
            case__isnull=False,
            **{f"{fk_field}__isnull": False},
        )
        .values(f"{fk_field}_id", f"{fk_field}__name")
        .annotate(cases_assigned=Count("case_id", distinct=True))
        .order_by(f"{fk_field}_id")
    )

    columns = [
        {"key": id_column, "label": _("id")},
        {"key": name_column, "label": _("name")},
        {"key": "cases_assigned", "label": _("cases assigned")},
        {"key": "cases_missing", "label": _("cases missing")},
    ]

    rows = []
    for entry in grouped:
        cases_assigned = entry["cases_assigned"]
        rows.append(
            {
                id_column: entry[f"{fk_field}_id"],
                name_column: entry[f"{fk_field}__name"],
                "cases_assigned": cases_assigned,
                "cases_missing": total_cases - cases_assigned,
            }
        )

    any_assigned = (
        Advice.objects.filter(
            case__created_on__year=year,
            case__isnull=False,
            **{f"{fk_field}__isnull": False},
        )
        .values("case_id")
        .distinct()
        .count()
    )
    rows.append(
        {
            id_column: "",
            name_column: str(ANY_TOTAL_LABEL),
            "cases_assigned": any_assigned,
            "cases_missing": total_cases - any_assigned,
            "pinned": True,
        }
    )

    return {"title": title, "columns": columns, "rows": rows}


def issues_report(year):
    return _m2m_case_breakdown(
        year, "issues", Issue, "issue_id", "issue_name", _("Issues report")
    )


def areas_report(year):
    return _m2m_case_breakdown(
        year, "area", Area, "area_id", "area_name", _("Areas report")
    )


def institution_kind_report(year):
    return _fk_case_breakdown(
        year,
        "institution_kind",
        InstitutionKind,
        "kind_id",
        "kind_name",
        _("Institution kind report"),
    )


def person_kind_report(year):
    return _fk_case_breakdown(
        year, "person_kind", PersonKind, "kind_id", "kind_name", _("Person kind report")
    )


def courtsessions_report():
    """Pivots court session counts into one column per distinct year found
    in the data, replicating the source SQL's dynamic prepared-statement
    pivot.
    """
    years = sorted(
        CourtSession.objects.exclude(created__isnull=True)
        .annotate(y=ExtractYear("created"))
        .values_list("y", flat=True)
        .distinct()
    )

    year_keys = [f"y_{year}" for year in years]
    annotations = {
        f"y_{year}": Count("id", filter=Q(created__year=year)) for year in years
    }

    grouped = (
        CourtSession.objects.values("parser_key")
        .annotate(**annotations, total=Count("id"))
        .order_by("parser_key")
    )

    columns = (
        [{"key": "parser_key", "label": _("parser key")}]
        + [{"key": f"y_{year}", "label": str(year)} for year in years]
        + [{"key": "total", "label": _("total")}]
    )

    rows = []
    totals = defaultdict(int)
    for entry in grouped:
        row = {"parser_key": entry["parser_key"] or str(NONE_LABEL)}
        for key in year_keys + ["total"]:
            row[key] = entry[key]
            totals[key] += entry[key]
        rows.append(row)

    rows.append({"parser_key": str(TOTAL_LABEL), **totals, "pinned": True})

    return {"title": _("Court sessions report"), "columns": columns, "rows": rows}


def courtcase_report():
    grouped = CourtCase.objects.values("court_id", "court__name").annotate(
        count=Count("id")
    )

    named_rows = []
    none_count = 0
    for entry in grouped:
        if entry["court_id"] is None:
            none_count += entry["count"]
        else:
            named_rows.append((entry["court__name"], entry["count"]))
    named_rows.sort(key=lambda item: item[0] or "")

    columns = [
        {"key": "court_name", "label": _("court")},
        {"key": "count", "label": _("count")},
    ]

    rows = [{"court_name": name, "count": count} for name, count in named_rows]
    if none_count:
        rows.append({"court_name": str(NONE_LABEL), "count": none_count})

    total = sum(count for _name, count in named_rows) + none_count
    rows.append({"court_name": str(TOTAL_LABEL), "count": total, "pinned": True})

    return {"title": _("Court cases report"), "columns": columns, "rows": rows}
