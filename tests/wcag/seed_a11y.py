#!/usr/bin/env python
"""Standalone seeder for the `poradnia_a11y` accessibility-audit database.

Not a management command on purpose (see logs/wcag/HANDOFF.md section 4) so it
stays outside the apps. Lives in tests/wcag/ (not logs/wcag/) because CI needs
it tracked in git - see logs/wcag/README.md §5. Run inside the `web`
container, from the repo root:

    docker compose -f docker-compose.yml -f tests/wcag/docker-compose.a11y.yml \
        run --rm web python tests/wcag/seed_a11y.py --reset

Requires env var A11Y_SEED_PASSWORD (never printed or written to disk).
"""

import argparse
import os
import random
import sys
import zipfile
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
DATA_DIR = REPO_ROOT / "logs" / "wcag" / "data"
README_PATH = REPO_ROOT / "logs" / "wcag" / "README.md"

sys.path.insert(0, str(REPO_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django  # noqa: E402

django.setup()

from allauth.account.models import EmailAddress  # noqa: E402
from django.conf import settings  # noqa: E402
from django.contrib.contenttypes.models import ContentType  # noqa: E402
from django.core.files import File  # noqa: E402
from django.utils import timezone  # noqa: E402
from guardian.shortcuts import assign_perm  # noqa: E402

from poradnia.advicer.models import (  # noqa: E402
    Advice,
    Area,
    InstitutionKind,
    Issue,
    PersonKind,
    Scope,
)
from poradnia.ai_assistant.models import N8nArticlesSearchRequest  # noqa: E402
from poradnia.cases.models import (  # noqa: E402
    Case,
    CaseGroupObjectPermission,
    CaseUserObjectPermission,
    PermissionGroup,
)
from poradnia.events.models import Event, Reminder  # noqa: E402
from poradnia.judgements.models import Court, CourtCase, CourtSession  # noqa: E402
from poradnia.keys.models import Key  # noqa: E402
from poradnia.letters.models import Attachment, Letter  # noqa: E402
from poradnia.records.models import Record  # noqa: E402
from poradnia.tasty_feedback.models import Feedback  # noqa: E402
from poradnia.users.factories import UserFactory  # noqa: E402
from poradnia.users.models import User  # noqa: E402

# Every table this script owns rows in. AUTO_INCREMENT on each is reset to 1
# after a --reset so pks are stable across resets (plain .delete() does not
# reset MySQL's auto_increment counter the way TRUNCATE does, and the sample
# URLs used by baseline_capture.js hardcode pks for specific seeded cases).
RESETTABLE_MODELS = [
    User,
    EmailAddress,
    Case,
    CaseUserObjectPermission,
    CaseGroupObjectPermission,
    Record,
    Letter,
    Attachment,
    Event,
    Reminder,
    Scope,
    Issue,
    Area,
    PersonKind,
    InstitutionKind,
    Advice,
    Court,
    CourtCase,
    CourtSession,
    Key,
    Feedback,
    N8nArticlesSearchRequest,
]

SEED_RANDOM_SEED = 1337

# Mirrors poradnia/cases/migrations/0021_initial_permission_group.py. That
# migration creates these PermissionGroup rows, but it runs *before*
# Django's post_migrate signal creates the custom Case permissions it looks
# up, so the groups end up with zero permissions attached on a fresh DB
# (confirmed: after `migrate` here, all four PermissionGroup rows had
# .permissions.count() == 0 even though the 15 case permissions already
# existed). This looks like a real bug in the app, worth flagging to Piotr,
# but out of scope for this audit. We fix it up here so staff-assignment
# scenarios in the seed data behave like the real "assign staff" UI intends.
#
# Second, separate bug: "can_view_all" is referenced all over the codebase
# (RecordQuerySet.for_user, AbstractRecordQuerySet.for_user, has_perm checks)
# but is never declared in Case.Meta.permissions, so the Permission row for
# it does not exist at all. No PermissionGroup can ever actually grant it;
# the lines below silently end up with fewer permissions than PERM_INITIAL
# lists for "wsparcie" and "obserwator" because of this. Also worth flagging
# to Piotr; also out of scope here.
PERM_INITIAL = {
    "wsparcie": ("can_add_record", "can_change_own_record", "can_view", "can_view_all"),
    "obserwator": ("can_view", "can_view_all"),
    "klient": ("can_add_record", "can_send_to_client", "can_view"),
    "admin": "__all__",
}


def assert_a11y_database():
    name = settings.DATABASES["default"]["NAME"]
    if not name.endswith("_a11y"):
        raise SystemExit(
            f"Refusing to run: DATABASE_URL points at {name!r}, not a *_a11y DB. "
            "Use tests/wcag/docker-compose.a11y.yml."
        )


def get_seed_password():
    password = os.environ.get("A11Y_SEED_PASSWORD")
    if not password:
        raise SystemExit(
            "A11Y_SEED_PASSWORD env var is required (not printed anywhere)."
        )
    return password


# ---------------------------------------------------------------------------
# Fake attachment files (no external services; Pillow is already a project
# dependency, so PDFs are produced as single-page image-only PDFs via
# Pillow's PDF writer rather than pulling in reportlab/fpdf. That also makes
# them a realistic example of a tagging failure for clause 10: an
# image-only page has no text layer, no tags, no reading order.)
# ---------------------------------------------------------------------------


def _make_png(path, text):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle((10, 10, 390, 190), outline=(0, 0, 0))
    draw.text((20, 90), text, fill=(0, 0, 0))
    img.save(path, "PNG")


def _make_image_only_pdf(path, text):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (800, 1100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), text, fill=(0, 0, 0))
    img.convert("RGB").save(path, "PDF")


def _make_docx(path, paragraphs):
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006'
        '/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        '/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml'
        '/2006/main">'
        f"<w:body>{body}</w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document)


def build_template_files():
    """(Re)generate the small set of reusable attachment source files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "sample.txt").write_text(
        "Przykładowa treść pisma do testów dostępności.\n"
        "Zawiera polskie znaki: ąćęłńóśźż ĄĆĘŁŃÓŚŹŻ.\n",
        encoding="utf-8",
    )
    _make_png(DATA_DIR / "sample.png", "WCAG test image")
    _make_image_only_pdf(DATA_DIR / "sample.pdf", "Przykladowy skan - sample.pdf")
    _make_image_only_pdf(
        DATA_DIR / "untagged.pdf",
        "Dokument bez tagow dostepnosci (clause 10 reference failure)",
    )
    _make_docx(
        DATA_DIR / "sample.docx",
        [
            "Przykladowe pismo w formacie docx.",
            "Drugi akapit z polskimi znakami: zazolc gesla jazn.",
        ],
    )
    return {
        "txt": DATA_DIR / "sample.txt",
        "png": DATA_DIR / "sample.png",
        "pdf": DATA_DIR / "sample.pdf",
        "untagged_pdf": DATA_DIR / "untagged.pdf",
        "docx": DATA_DIR / "sample.docx",
    }


def attach_file(letter, path):
    with open(path, "rb") as fh:
        return Attachment.objects.create(
            letter=letter, attachment=File(fh, name=path.name)
        )


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def reset_database():
    """Wipe all seed-owned data.

    Deletes every User, relying on Django's cascade collector to follow the
    on_delete=CASCADE chain through Case/Letter/Attachment/Record/Event/
    Reminder/CaseUserObjectPermission/CaseGroupObjectPermission/Advice/
    CourtCase/CourtSession/Key/Feedback/EmailAddress. This resolves FK order
    automatically instead of a hand-maintained TRUNCATE list, which is safer
    given how many models hang off a user FK in this schema. What's left
    over (Court, and the advicer taxonomy models, which have no user FK) is
    cleared explicitly. PermissionGroup rows are left alone; they get
    upserted idempotently by ensure_permission_groups().

    Django never deletes a FileField/ImageField's underlying file when the
    row is deleted (by design, in case other rows reference the same file),
    so without this every --reset orphaned the previous run's avatars and
    attachments on disk. Both UserFactory's avatar and attach_file()'s
    attachments are named deterministically (by username, and by the fixed
    sample.{png,docx,...} fixture names respectively - not randomly), so the
    next --reset's .objects.create() collides with the leftover file and
    Django's storage backend appends a random suffix to disambiguate -
    confirmed live as the cause of a wcag_mode_checks baseline flake (the
    avatar's sorl-thumbnail cache path and the attachment's downloadable
    filename are both keyed off this exact filename, so a new random suffix
    meant different output on every run, appearing as spurious content
    diffs on any page showing an avatar or an attachment link). Deleted
    per-object via each FileField's own .delete() rather than a blanket
    filesystem wipe of avatars/ or the attachment upload dir: those are
    plain filesystem paths, shared on a local dev machine with whichever
    other database "web" happens to be pointed at, so only removing exactly
    the files these rows own is safe.
    """
    for user in User.objects.exclude(picture=""):
        user.picture.delete(save=False)
    for attachment in Attachment.objects.exclude(attachment=""):
        attachment.attachment.delete(save=False)
    User.objects.all().delete()
    CourtSession.objects.all().delete()
    CourtCase.objects.all().delete()
    Court.objects.all().delete()
    Advice.objects.all().delete()
    # Feedback.user is nullable: rows created with user=None (the
    # "anonymous feedback" scenario) aren't reachable by cascading from
    # User, so they'd otherwise survive every --reset and accumulate.
    Feedback.objects.all().delete()
    # N8nArticlesSearchRequest.case/.letter are on_delete=SET_NULL, not
    # CASCADE, so these rows also survive a User/Case/Letter wipe untouched.
    N8nArticlesSearchRequest.objects.all().delete()
    for model in (Scope, Issue, Area, PersonKind, InstitutionKind):
        model.objects.all().delete()
    reset_autoincrement()


def reset_autoincrement():
    from django.db import connection

    with connection.cursor() as cursor:
        for model in RESETTABLE_MODELS:
            table = model._meta.db_table
            cursor.execute(f"ALTER TABLE `{table}` AUTO_INCREMENT = 1")


def ensure_permission_groups():
    content_type = ContentType.objects.get_for_model(Case)
    from django.contrib.auth.models import Permission

    for name, codenames in PERM_INITIAL.items():
        group, _ = PermissionGroup.objects.get_or_create(name=name)
        if codenames == "__all__":
            perms = Permission.objects.filter(content_type=content_type)
        else:
            perms = Permission.objects.filter(
                content_type=content_type, codename__in=codenames
            )
        group.permissions.set(perms)
    return {g.name: g for g in PermissionGroup.objects.all()}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

LOGIN_ROWS = []  # (username, email, role, purpose) for the checkpoint table


def _record_login(user, role, purpose):
    LOGIN_ROWS.append((user.username, user.email, role, purpose))


def verify_email(user):
    EmailAddress.objects.create(
        user=user, email=user.email, verified=True, primary=True
    )


def create_users(password):
    users = {}

    users["superuser"] = UserFactory(
        username="a11y_superuser",
        first_name="Anna",
        last_name="Administrator",
        is_staff=True,
        is_superuser=True,
        password=password,
    )
    verify_email(users["superuser"])
    _record_login(
        users["superuser"],
        "superuser",
        "Full Django admin access; admin:* pages, admin case delete",
    )

    users["staff_admin"] = UserFactory(
        username="a11y_staff_admin",
        first_name="Bartosz",
        last_name="Kierownik",
        is_staff=True,
        password=password,
    )
    verify_email(users["staff_admin"])
    # tasty_feedback:list/:details/:status require the Django model
    # permissions directly (tasty_feedback.view_feedback / .change_feedback),
    # not a cases.PermissionGroup -- confirmed live (403 without this).
    from django.contrib.auth.models import Permission as DjangoPermission

    users["staff_admin"].user_permissions.add(
        *DjangoPermission.objects.filter(
            content_type__app_label="tasty_feedback",
            codename__in=["view_feedback", "change_feedback"],
        )
    )
    _record_login(
        users["staff_admin"],
        "staff (admin group)",
        "Staff member granted the 'admin' PermissionGroup (all case perms) on some"
        " cases + tasty_feedback.view/change_feedback",
    )

    users["staff_wsparcie"] = UserFactory(
        username="a11y_staff_wsparcie",
        first_name="Celina",
        last_name="Wsparcie",
        is_staff=True,
        password=password,
    )
    verify_email(users["staff_wsparcie"])
    _record_login(
        users["staff_wsparcie"],
        "staff (wsparcie group)",
        "Staff member granted the 'wsparcie' PermissionGroup; drafts/sends letters",
    )

    users["staff_obserwator"] = UserFactory(
        username="a11y_staff_obserwator",
        first_name="Dawid",
        last_name="Obserwator",
        is_staff=True,
        password=password,
    )
    verify_email(users["staff_obserwator"])
    _record_login(
        users["staff_obserwator"],
        "staff (obserwator group)",
        "Read-only staff: 'obserwator' PermissionGroup (can_view only - see note on"
        " cases.can_view_all below)",
    )

    users["client_active"] = UserFactory(
        username="a11y_client_active",
        first_name="Ewa",
        last_name="Klientka",
        password=password,
    )
    verify_email(users["client_active"])
    _record_login(
        users["client_active"],
        "client",
        "Active client with many cases — case list/detail pagination testing",
    )

    users["client_empty"] = UserFactory(
        username="a11y_client_empty",
        first_name="Filip",
        last_name="Bezsprawy",
        password=password,
    )
    verify_email(users["client_empty"])
    _record_login(
        users["client_empty"], "client", "Client with zero cases — empty-state testing"
    )

    users["client_longname"] = UserFactory(
        username="a11y_client_longname",
        first_name="Zofia",
        last_name="Świętosławska-Grzegorzewska-Łączyńska",
        password=password,
    )
    verify_email(users["client_longname"])
    _record_login(
        users["client_longname"],
        "client",
        "Long diacritic name — truncation/overflow testing",
    )

    # Unusable password, no EmailAddress row at all: the exact state left by
    # a real inbound-email-created client who hasn't followed the activation
    # link yet. See User.objects.register_by_email and
    # AccountActivationView.form_valid in poradnia/users/views.py.
    users["client_unverified"] = User.objects.register_by_email(
        email="a11y_client_unverified@example.com", notify=False
    )
    users["client_unverified"].first_name = "Grzegorz"
    users["client_unverified"].last_name = "Nieaktywowany"
    users["client_unverified"].save()
    _record_login(
        users["client_unverified"],
        "client (unactivated)",
        "Unusable password, no verified e-mail — account-activation flow testing",
    )

    return users


# ---------------------------------------------------------------------------
# Cases / letters / attachments
# ---------------------------------------------------------------------------

POLISH_SUBJECT_WORDS = [
    "Wniosek o informację publiczną",
    "Skarga na bezczynność urzędu",
    "Dostęp do danych środowiskowych",
    "Zażalenie na odmowę",
    "Prośba o udostępnienie rejestru",
    "Sprawa dotycząca ponownego wykorzystania",
    "Żądanie wyjaśnień urzędu gminy",
    "Odwołanie od decyzji wójta",
    "Pytanie o wydatki publiczne",
    "Zapytanie o uchwałę rady miasta",
]


def grant_group(user, case, group):
    for perm in group.permissions.all():
        assign_perm(perm, user, case)
    case.update_status(save=True)


def create_case(client, created_by, name, status=None):
    case = Case.objects.create(name=name, client=client, created_by=created_by)
    if status is not None:
        case.status = status
        case.save()
    return case


def create_letter(case, created_by, genre, status, name, text):
    return Letter.objects.create(
        case=case,
        created_by=created_by,
        created_by_is_staff=created_by.is_staff,
        genre=genre,
        status=status,
        name=name,
        text=text,
        signature="",
    )


def create_scenario_cases(users, groups, files):
    cases = {}

    # 1-message thread, unassigned (free).
    case = create_case(
        users["client_active"],
        users["client_active"],
        "Wniosek o udostępnienie rejestru umów",
    )
    create_letter(
        case,
        users["client_active"],
        "mail",
        Letter.STATUS.done,
        "Wniosek o udostępnienie rejestru umów",
        "Proszę o udostępnienie rejestru umów zawartych w 2026 roku.",
    )
    cases["thread1"] = case

    # 5-message thread covering every genre and both statuses.
    case = create_case(
        users["client_active"],
        users["client_active"],
        "Spór o dostęp do danych środowiskowych",
    )
    grant_group(users["staff_wsparcie"], case, groups["wsparcie"])
    genre_status_plan = [
        ("mail", Letter.STATUS.done, users["client_active"]),
        ("comment", Letter.STATUS.staff, users["staff_wsparcie"]),
        ("app_message", Letter.STATUS.done, users["client_active"]),
        ("ai_message_staff", Letter.STATUS.staff, users["staff_wsparcie"]),
        ("ai_message", Letter.STATUS.done, users["staff_wsparcie"]),
    ]
    first_letter = None
    for i, (genre, status, author) in enumerate(genre_status_plan):
        letter = create_letter(
            case,
            author,
            genre,
            status,
            f"Pismo {i + 1} w sprawie danych środowiskowych",
            f"Treść pisma numer {i + 1} (genre={genre}, status={status}).",
        )
        if i == 0:
            first_letter = letter
    attach_file(first_letter, files["png"])
    attach_file(first_letter, files["docx"])
    cases["thread5"] = case

    # 25-message thread, for DataTables-style pagination within a case.
    case = create_case(
        users["client_active"],
        users["client_active"],
        "Długotrwała korespondencja ws. decyzji administracyjnej",
    )
    grant_group(users["staff_admin"], case, groups["admin"])
    genres = [g[0] for g in Letter.GENRE]
    statuses = [Letter.STATUS.done, Letter.STATUS.staff]
    letters = []
    for i in range(25):
        author = users["client_active"] if i % 3 == 0 else users["staff_admin"]
        letter = create_letter(
            case,
            author,
            genres[i % len(genres)],
            statuses[i % len(statuses)],
            f"Pismo nr {i + 1} w długiej korespondencji",
            f"Treść pisma numer {i + 1} z 25 w tej sprawie.",
        )
        letters.append(letter)
    attach_file(letters[0], files["txt"])
    attach_file(letters[-1], files["pdf"])
    # The clause-10 reference failure: attached to a staff-authored letter so
    # it reads as an organisation-produced document, not a client upload
    # (client uploads are explicitly out of clause-10 scope per HANDOFF §1).
    staff_letter = next(
        letter for letter in letters if letter.created_by_id == users["staff_admin"].id
    )
    attach_file(staff_letter, files["untagged_pdf"])
    # Pending AI-articles-search request on an ai_message letter: this is
    # what makes the accept/reject thumbs-up/down UI (and the "reject"
    # modal) actually render -- Letter.get_ai_search_request() returns None
    # otherwise, confirmed by reading _letter_ai_feedback.html's
    # {% if search_request %} gate. Created directly via the ORM with
    # accepted_at/rejected_at left null (pending); never calls
    # N8nArticlesSearchRequest.search_articles(), which is the only thing
    # that would actually hit the n8n webhook.
    ai_letter = next(
        letter
        for letter in letters
        if letter.genre == "ai_message" and letter.status == Letter.STATUS.staff
    )
    N8nArticlesSearchRequest.objects.create(
        request_id="a11y-seed-request-1",
        environment="DEV",
        question="Czy urząd musi udostępnić rejestr umów na żądanie?",
        case=case,
        letter=ai_letter,
        status="completed",
        response="Tak, zgodnie z art. 6 ustawy o dostępie do informacji publicznej.",
    )
    cases["thread25"] = case

    # Closed case.
    case = create_case(
        users["client_active"],
        users["client_active"],
        "Sprawa zamknięta po udzieleniu odpowiedzi",
    )
    grant_group(users["staff_wsparcie"], case, groups["wsparcie"])
    create_letter(
        case,
        users["client_active"],
        "mail",
        Letter.STATUS.done,
        "Pytanie o decyzję",
        "Proszę o wyjaśnienie decyzji z zeszłego miesiąca.",
    )
    create_letter(
        case,
        users["staff_wsparcie"],
        "mail",
        Letter.STATUS.done,
        "Odpowiedź i zamknięcie sprawy",
        "Sprawa została wyjaśniona i zamykamy wątek.",
    )
    case.status = Case.STATUS.closed
    case.save()
    cases["closed"] = case

    # Moderated: a staff member has *some* permission but not can_send_to_client.
    case = create_case(
        users["client_active"], users["client_active"], "Sprawa w moderacji"
    )
    grant_group(users["staff_obserwator"], case, groups["obserwator"])
    cases["moderated"] = case

    # Max-length subject (NAME_MAX_LENGTH == 250).
    long_name = (
        "Wniosek o udostępnienie informacji publicznej dotyczącej wydatków " * 10
    )[:250]
    cases["maxlen"] = create_case(
        users["client_active"], users["client_active"], long_name
    )

    # Diacritics-heavy subject.
    cases["diacritics"] = create_case(
        users["client_longname"],
        users["client_longname"],
        "Żądanie dostępu do dokumentów dotyczących śmieci i ścieków w gminie Łęczyca",
    )

    # Raw-HTML-in-subject, for 4.1.1 parsing / escaping checks.
    cases["xss"] = create_case(
        users["client_active"],
        users["client_active"],
        "Przykładowa sprawa <b>test</b> do testów renderowania",
    )

    # Client with zero cases stays untouched (no Case created for them).
    return cases


def create_bulk_cases(users, groups, target_total):
    existing = Case.objects.count()
    to_create = max(0, target_total - existing)
    staff_cycle = [
        ("wsparcie", "staff_wsparcie"),
        ("obserwator", "staff_obserwator"),
        ("admin", "staff_admin"),
        (None, None),
    ]
    for i in range(to_create):
        subject = f"{random.choice(POLISH_SUBJECT_WORDS)} nr {i + 1}"
        case = create_case(users["client_active"], users["client_active"], subject)
        group_name, staff_key = staff_cycle[i % len(staff_cycle)]
        if group_name:
            grant_group(users[staff_key], case, groups[group_name])
        if i % 4 == 2:
            # A few cases get a second staff member too.
            grant_group(users["staff_admin"], case, groups["admin"])
        if i % 5 == 0:
            create_letter(
                case,
                users["client_active"],
                "mail",
                Letter.STATUS.done,
                f"Pierwsze pismo w sprawie nr {i + 1}",
                "Treść pierwszego pisma w tej sprawie.",
            )


# ---------------------------------------------------------------------------
# Events, advicer, judgements, keys, feedback
# ---------------------------------------------------------------------------


def create_events(users, cases):
    now = timezone.now()
    past = Event.objects.create(
        case=cases["thread5"],
        text="Termin, który już minął",
        deadline=True,
        time=now - timezone.timedelta(days=10),
        created_by=users["staff_wsparcie"],
    )
    today = Event.objects.create(
        case=cases["thread25"],
        text="Termin przypadający dzisiaj",
        deadline=True,
        time=now,
        created_by=users["staff_admin"],
    )
    future = Event.objects.create(
        case=cases["closed"],
        text="Przyszłe wydarzenie",
        deadline=False,
        time=now + timezone.timedelta(days=30),
        created_by=users["staff_wsparcie"],
        public=True,
    )
    Reminder.objects.create(user=users["staff_wsparcie"], event=future)
    return {"past": past, "today": today, "future": future}


def create_advicer_data(users, cases):
    scope = Scope.objects.create(name="Dostęp do informacji publicznej")
    issue = Issue.objects.create(name="Odmowa udostępnienia")
    area = Area.objects.create(name="Administracja samorządowa")
    person_kind = PersonKind.objects.create(name="Osoba fizyczna")
    institution_kind = InstitutionKind.objects.create(name="Urząd gminy")

    advice = Advice.objects.create(
        case=cases["thread5"],
        subject="Porada ws. danych środowiskowych",
        summary="Udzielono porady dotyczącej zakresu informacji środowiskowej.",
        person_kind=person_kind,
        institution_kind=institution_kind,
        advicer=users["staff_wsparcie"],
        created_by=users["staff_wsparcie"],
        visible=True,
    )
    advice.issues.add(issue)
    advice.area.add(area)

    advice2 = Advice.objects.create(
        subject="Porada ogólna bez przypisanej sprawy",
        summary="Porada nie powiązana z konkretną sprawą.",
        advicer=users["staff_obserwator"],
        created_by=users["staff_obserwator"],
        visible=True,
    )
    return {"scope": scope, "advices": [advice, advice2]}


def create_judgements_data(users, cases, events):
    court = Court.objects.create(
        name="Wojewódzki Sąd Administracyjny w Warszawie", parser_key=""
    )
    court_case = CourtCase.objects.create(
        case=cases["thread25"],
        court=court,
        signature="II SAB/Wa 12/26",
        created_by=users["staff_admin"],
    )
    CourtSession.objects.create(
        courtcase=court_case, event=events["today"], parser_key=""
    )
    return {"court": court, "court_case": court_case}


def create_keys(users):
    Key.objects.create(
        user=users["client_active"], description="Klucz do integracji testowej"
    )
    Key.objects.create(user=users["staff_wsparcie"], description="Klucz API personelu")


def create_feedback(users):
    Feedback.objects.create(
        user=users["client_active"],
        url="/cases/",
        text="Trudno znaleźć przycisk odpowiedzi.",
        status=False,
    )
    Feedback.objects.create(
        user=users["staff_wsparcie"],
        url="/cases/1/",
        text="Lista pism ładuje się długo.",
        status=True,
    )
    Feedback.objects.create(
        user=None,
        url="/",
        text="Zgłoszenie anonimowe o problemie z kontrastem.",
        status=False,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def render_login_table():
    lines = ["| username | email | role | purpose |", "|---|---|---|---|"]
    for username, email, role, purpose in LOGIN_ROWS:
        lines.append(f"| `{username}` | {email} | {role} | {purpose} |")
    return "\n".join(lines)


LOGIN_MARKER_BEGIN = "<!-- SEED_LOGINS:BEGIN -->"
LOGIN_MARKER_END = "<!-- SEED_LOGINS:END -->"


def write_logins_to_readme(table_markdown):
    section = (
        f"{LOGIN_MARKER_BEGIN}\n"
        "<!-- Generated by tests/wcag/seed_a11y.py. Do not edit by hand. -->\n"
        "<!-- Passwords are never recorded here: use the A11Y_SEED_PASSWORD env"
        " var. -->\n\n"
        f"{table_markdown}\n\n"
        f"{LOGIN_MARKER_END}\n"
    )
    if README_PATH.exists():
        content = README_PATH.read_text(encoding="utf-8")
    else:
        content = "# WCAG audit — logins and commands\n\n"
    if LOGIN_MARKER_BEGIN in content and LOGIN_MARKER_END in content:
        before = content.split(LOGIN_MARKER_BEGIN)[0]
        after = content.split(LOGIN_MARKER_END)[1]
        content = before + section + after
    else:
        content = content.rstrip() + "\n\n" + section
    README_PATH.write_text(content, encoding="utf-8")


EXPECTED_MINIMUMS = {
    "User": 8,
    "Case": 60,
    "Letter": 30,
    "Attachment": 4,
    "Event": 3,
    "Reminder": 1,
    "Advice": 2,
    "CourtCase": 1,
    "CourtSession": 1,
    "Key": 2,
    "Feedback": 3,
    "PermissionGroup": 4,
    "N8nArticlesSearchRequest": 1,
}


def self_check():
    from poradnia.cases.models import Case as CaseModel

    counts = {
        "User": User.objects.count(),
        "Case": CaseModel.objects.count(),
        "Letter": Letter.objects.count(),
        "Attachment": Attachment.objects.count(),
        "Event": Event.objects.count(),
        "Reminder": Reminder.objects.count(),
        "Advice": Advice.objects.count(),
        "CourtCase": CourtCase.objects.count(),
        "CourtSession": CourtSession.objects.count(),
        "Key": Key.objects.count(),
        "Feedback": Feedback.objects.count(),
        "PermissionGroup": PermissionGroup.objects.count(),
        "N8nArticlesSearchRequest": N8nArticlesSearchRequest.objects.count(),
    }
    ok = True
    print(f"{'model':<16} {'count':>6} {'min':>6}  status")
    for model, minimum in EXPECTED_MINIMUMS.items():
        count = counts[model]
        passed = count >= minimum
        ok = ok and passed
        print(f"{model:<16} {count:>6} {minimum:>6}  {'PASS' if passed else 'FAIL'}")
    groups_with_perms = [
        g.name for g in PermissionGroup.objects.all() if g.permissions.count() == 0
    ]
    if groups_with_perms:
        ok = False
        print(f"FAIL: PermissionGroup(s) with zero permissions: {groups_with_perms}")
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def seed(password):
    random.seed(SEED_RANDOM_SEED)
    files = build_template_files()
    groups = ensure_permission_groups()
    users = create_users(password)
    cases = create_scenario_cases(users, groups, files)
    create_bulk_cases(users, groups, target_total=65)
    events = create_events(users, cases)
    create_advicer_data(users, cases)
    create_judgements_data(users, cases, events)
    create_keys(users)
    create_feedback(users)

    table = render_login_table()
    write_logins_to_readme(table)
    print(table)
    print(f"\nTotal cases: {Case.objects.count()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="Wipe and re-seed.")
    parser.add_argument(
        "--self-check",
        action="store_true",
        dest="self_check",
        help="Only verify row counts against expected minimums; no writes.",
    )
    args = parser.parse_args()

    assert_a11y_database()

    if args.self_check and not args.reset:
        sys.exit(0 if self_check() else 1)

    if Case.objects.exists() and not args.reset:
        raise SystemExit(
            "poradnia_a11y already has Case rows. Pass --reset to wipe and re-seed."
        )

    password = get_seed_password()

    if args.reset:
        reset_database()

    seed(password)

    if args.self_check:
        sys.exit(0 if self_check() else 1)


if __name__ == "__main__":
    main()
