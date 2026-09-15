"""Hardcoded catalog of every outbound e-mail template in the app, used by
the staff-only preview page at /admin/email-catalog/ (see views.py).

This list is maintained by hand. If you add, rename or remove an e-mail
template anywhere in the app, update the matching entry here too.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional

from django.conf import settings


class Mock:
    """Duck-typed stand-in for a model instance, used only to build a
    realistic preview context without touching the database."""

    def __init__(self, str_value="", **attrs):
        self._str_value = str_value
        self.__dict__.update(attrs)

    def __str__(self):
        return self._str_value


@dataclass
class EmailCatalogEntry:
    group: str
    key: str
    title: str
    trigger: str
    sender: Optional[str] = None  # who/what address the e-mail is sent from
    recipient: Optional[str] = None  # who the e-mail is sent to
    txt_template: Optional[str] = None
    html_template: Optional[str] = None
    subject_template: Optional[str] = None  # allauth-style: subject rendered separately
    split_subject: bool = (
        False  # TemplateMailManager-style: subject = first line of txt
    )
    context: Callable[[], dict] = field(default=dict)
    note: Optional[str] = None
    raw_example: Optional[str] = None  # for entries with no Django template at all


def _case(client=None):
    return Mock(
        "#123 Wniosek o dostęp do informacji publicznej",
        client=client or Mock("Jan Kowalski"),
        get_absolute_url=lambda: "/sprawy/123/",
    )


def _attachment_set():
    attachment = Mock(
        "wniosek.pdf",
        get_full_url=lambda: (
            "https://poradnia.siecobywatelska.pl/media/przyklad/wniosek.pdf"
        ),
    )
    return Mock(all=lambda: [attachment])


def _letter(actor_is_staff=False, client=None):
    if actor_is_staff:
        return Mock(
            "Odpowiedź na pytanie",
            name="Odpowiedź na pytanie",
            text=(
                "Szanowni Państwo,\n\nw odpowiedzi na pytanie uprzejmie informujemy..."
            ),
            created_by=Mock("Anna Nowak (Poradnia)"),
            case=_case(client=client),
            get_absolute_url=lambda: "/sprawy/123/#pismo-456",
            attachment_set=_attachment_set(),
            render_as_html=lambda: (
                "<p>Szanowni Państwo,</p><p>w odpowiedzi na pytanie uprzejmie "
                "informujemy...</p>"
            ),
        )
    return Mock(
        "Pytanie w sprawie o dostęp do informacji publicznej",
        name="Pytanie w sprawie o dostęp do informacji publicznej",
        text=(
            "Szanowni Państwo,\n\nzwracam się z pytaniem w sprawie o udostępnienie "
            "informacji publicznej..."
        ),
        created_by=Mock("Jan Kowalski"),
        case=_case(client=client),
        get_absolute_url=lambda: "/sprawy/123/#pismo-456",
        attachment_set=_attachment_set(),
        render_as_html=lambda: (
            "<p>Szanowni Państwo,</p><p>zwracam się z pytaniem w sprawie o "
            "udostępnienie informacji publicznej...</p>"
        ),
    )


def _actor(is_staff=False):
    return Mock(
        "Anna Nowak (Poradnia)" if is_staff else "Jan Kowalski", is_staff=is_staff
    )


def _unactivated_client():
    """A client whose account has no usable password yet (e.g. auto-created
    from an inbound e-mail) - used to preview the activation-link block
    shared by letter_created/letter_updated/letter_send_to_client (see
    _activation_link.html/.txt)."""
    return Mock(
        "Jan Kowalski",
        has_usable_password=lambda: False,
        get_activation_path=lambda: "/uzytkownik/aktywuj/MQ/abc123-token/",
    )


def _unactivated_client_context():
    client = _unactivated_client()
    return {
        "target": _letter(actor_is_staff=True, client=client),
        "actor": _actor(is_staff=True),
        "user": client,
    }


def _event():
    return Mock(
        "Termin odpowiedzi na wniosek",
        text="Upływa ustawowy termin na udzielenie odpowiedzi.",
        time="2026-08-01 12:00",
        case=_case(),
        get_absolute_url=lambda: "/sprawy/123/wydarzenia/45/",
    )


def _notification_meta(**extra):
    return {
        "ip": "192.0.2.10",
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101",
        "timestamp": "2026-07-24 12:00:00",
        **extra,
    }


# Sender text reused by every "case address" e-mail (TemplateMailManager /
# Case.send_notification always builds the From header as the case's own
# inbound address, display-named as the acting user - see cases/models.py).
_CASE_ADDRESS_SENDER = (
    "adres sprawy (sprawa-{id}@...), jako wyświetlana nazwa nadawcy "
    "widnieje osoba wykonująca akcję"
)
_DEFAULT_SENDER = (
    f"domyślny adres nadawcy systemu (ustawienie DEFAULT_FROM_EMAIL: "
    f"{settings.DEFAULT_FROM_EMAIL})"
)
_ALLAUTH_SENDER = _DEFAULT_SENDER + " (allauth)"
_MANAGERS_RECIPIENT = "adresy z ustawienia MANAGERS: " + (
    ", ".join(email for _, email in settings.MANAGERS)
    or "(brak skonfigurowanych adresów)"
)
_SERVER_EMAIL_DISPLAY = settings.SERVER_EMAIL or "(pusty ciąg — nieustawione)"
_SERVER_EMAIL_SENDER = (
    f"ustawienie SERVER_EMAIL ({_SERVER_EMAIL_DISPLAY}); nagłówek Reply-To "
    "wskazuje na adres zgłaszającego"
)


CATALOG = [
    # -- Sprawy (cases) ------------------------------------------------
    EmailCatalogEntry(
        group="Sprawy",
        key="case_new",
        title="Nowa sprawa w systemie",
        trigger=(
            "Sygnał post_save modelu Case (cases/models.py: notify_new_case) - "
            "wysyłane natychmiast po utworzeniu nowej sprawy, do wszystkich "
            "użytkowników z profilowym ustawieniem „Powiadamiaj o nowych "
            "sprawach” (User.notify_new_case=True)."
        ),
        sender=_DEFAULT_SENDER,
        recipient=(
            "użytkownicy z ustawieniem „Powiadamiaj o nowych sprawach” "
            "(User.notify_new_case=True)"
        ),
        txt_template="cases/email/case_new.txt",
        html_template="cases/email/case_new.html",
        split_subject=True,
        context=lambda: {"case": _case()},
    ),
    EmailCatalogEntry(
        group="Sprawy",
        key="case_registered",
        title="Potwierdzenie zarejestrowania sprawy (do klienta)",
        trigger=(
            "NewCaseCreateView.formset_valid (letters/views/cbv.py) - wysyłane "
            "do klienta po zarejestrowaniu nowej sprawy, o ile jego konto ma już "
            "ustawione hasło (client.has_usable_password())."
        ),
        sender=_CASE_ADDRESS_SENDER + " (osoba rejestrująca sprawę)",
        recipient="klient (tylko jeśli jego konto ma już ustawione hasło)",
        txt_template="cases/email/case_registered.txt",
        html_template="cases/email/case_registered.html",
        split_subject=True,
        context=lambda: {
            "target": _case(),
            "actor": _actor(is_staff=True),
            "user": Mock("Jan Kowalski"),
            "email": "sprawa-123@example.poradnia.pl",
        },
    ),
    EmailCatalogEntry(
        group="Sprawy",
        key="case_closed",
        title="Sprawa zamknięta",
        trigger=(
            "Case.close() (cases/models.py) - wysyłane, gdy sprawa zostanie "
            "zamknięta."
        ),
        sender=_CASE_ADDRESS_SENDER + " (osoba zamykająca sprawę)",
        recipient=(
            "wszyscy użytkownicy z jakimikolwiek uprawnieniami do sprawy "
            "(także klient)"
        ),
        txt_template="cases/email/case_closed.txt",
        html_template="cases/email/case_closed.html",
        split_subject=True,
        context=dict,
    ),
    EmailCatalogEntry(
        group="Sprawy",
        key="case_updated",
        title="Sprawa zaktualizowana",
        trigger=(
            "CaseForm.save() (cases/forms.py) - wysyłane do przypisanego "
            "personelu, gdy sprawa w statusie „przypisana” zostanie zmieniona."
        ),
        sender=_CASE_ADDRESS_SENDER + " (osoba edytująca sprawę)",
        recipient="przypisany personel sprawy (bez klienta)",
        txt_template="cases/email/case_updated.txt",
        html_template="cases/email/case_updated.html",
        split_subject=True,
        context=lambda: {"target": _case(), "actor": _actor(is_staff=True)},
    ),
    EmailCatalogEntry(
        group="Sprawy",
        key="case_granted",
        title="Nadano uprawnienia do sprawy",
        trigger=(
            "UserPermissionCreateView.form_valid (cases/views/permissions.py) - "
            "wysyłane do personelu, gdy ktoś nada użytkownikowi uprawnienia "
            "do sprawy."
        ),
        sender=_CASE_ADDRESS_SENDER + " (osoba nadająca uprawnienia)",
        recipient="personel z uprawnieniami do sprawy",
        txt_template="cases/email/case_granted.txt",
        html_template="cases/email/case_granted.html",
        split_subject=True,
        context=lambda: {"target": _case(), "actor": _actor(is_staff=True)},
    ),
    EmailCatalogEntry(
        group="Sprawy",
        key="case_grant_group",
        title="Nadano uprawnienia grupy do sprawy",
        trigger=(
            "CaseGroupPermissionForm.assign (cases/forms.py) - wysyłane do "
            "przypisanego personelu, gdy użytkownikowi zostanie nadana grupa "
            "uprawnień (np. „opiekun”) w konkretnej sprawie."
        ),
        sender=_CASE_ADDRESS_SENDER + " (osoba nadająca uprawnienia)",
        recipient="przypisany personel sprawy",
        txt_template="cases/email/case_grant_group.txt",
        html_template="cases/email/case_grant_group.html",
        split_subject=True,
        context=lambda: {
            "target": _case(),
            "actor": _actor(is_staff=True),
            "action_object": Mock("Jan Kowalski"),
            "action_target": Mock("Opiekun sprawy"),
        },
    ),
    EmailCatalogEntry(
        group="Sprawy",
        key="case_delete_old",
        title="Przypomnienie o starych sprawach do skasowania",
        trigger=(
            "Okresowe zadanie celery send_old_cases_reminder (cases/tasks.py) - "
            "wysyłane do użytkowników z ustawieniem „Powiadamiaj o starych "
            "sprawach” (User.notify_old_cases=True), gdy w systemie są sprawy "
            "bez aktywności dłużej niż YEARS_TO_STORE_CASES lat."
        ),
        sender=_DEFAULT_SENDER,
        recipient=(
            "użytkownicy z ustawieniem „Powiadamiaj o starych sprawach” "
            "(User.notify_old_cases=True)"
        ),
        txt_template="cases/email/case_delete_old.txt",
        html_template="cases/email/case_delete_old.html",
        split_subject=True,
        context=dict,
    ),
    # -- Wydarzenia (events) --------------------------------------------
    EmailCatalogEntry(
        group="Wydarzenia",
        key="event_created",
        title="Nowe wydarzenie w sprawie",
        trigger=(
            "EventForm.save() (events/forms.py) - wysyłane przy utworzeniu "
            "wydarzenia."
        ),
        sender=_CASE_ADDRESS_SENDER + " (osoba tworząca wydarzenie)",
        recipient="przypisany personel sprawy",
        txt_template="events/email/event_created.txt",
        html_template="events/email/event_created.html",
        split_subject=True,
        context=lambda: {"target": _event(), "actor": _actor(is_staff=True)},
    ),
    EmailCatalogEntry(
        group="Wydarzenia",
        key="event_updated",
        title="Wydarzenie zaktualizowane",
        trigger=(
            "EventForm.save() (events/forms.py) - wysyłane przy edycji "
            "istniejącego wydarzenia."
        ),
        sender=_CASE_ADDRESS_SENDER + " (osoba edytująca wydarzenie)",
        recipient="przypisany personel sprawy",
        txt_template="events/email/event_updated.txt",
        html_template="events/email/event_updated.html",
        split_subject=True,
        context=lambda: {"target": _event(), "actor": _actor(is_staff=True)},
    ),
    EmailCatalogEntry(
        group="Wydarzenia",
        key="event_reminder",
        title="Przypomnienie o zbliżającym się terminie",
        trigger=(
            "Okresowe zadanie celery send_event_reminders (events/tasks.py) - "
            "wysyłane, gdy do terminu wydarzenia zostało mniej niż "
            "profil.event_reminder_time dni (domyślnie 1 dzień)."
        ),
        sender=_CASE_ADDRESS_SENDER + " (jako nadawca widnieje sam odbiorca)",
        recipient=(
            "personel z uprawnieniami do sprawy (w pierwszej kolejności osoby "
            "mogące wysyłać do klienta), z fallbackiem do użytkowników z "
            "ustawieniem „Powiadamiaj o nieprzypisanych pismach”"
        ),
        txt_template="events/email/event_reminder.txt",
        html_template="events/email/event_reminder.html",
        split_subject=True,
        context=lambda: {"target": _event(), "actor": _actor()},
    ),
    # -- Pisma (letters) --------------------------------------------------
    EmailCatalogEntry(
        group="Pisma",
        key="letter_created",
        title="Nowe pismo w sprawie",
        trigger=(
            "ReceiveEmailView.post (letters/views/cbv.py) - wysyłane, gdy w "
            "sprawie pojawi się nowe pismo przychodzące przez IMAP/webhook "
            "(zwykle e-mail od klienta, ale też odpowiedź pracownika "
            "wysłana zwykłą pocztą zamiast przyciskiem „Wyślij”). Jeśli "
            "nadawcą jest pracownik z uprawnieniem can_send_to_client, "
            "pismo od razu ma status „done” i trafia też do klienta - "
            "wtedy pojawia się ten sam dopisek o aktywacji konta co w "
            "letter_send_to_client, zob. wpis niżej."
        ),
        sender=_CASE_ADDRESS_SENDER + " (autor pisma)",
        recipient=(
            "personel przypisany do sprawy; klient dodatkowo, jeśli pismo od "
            "razu ma status „gotowe” (zob. opis wyzwalacza)"
        ),
        txt_template="letters/email/letter_created.txt",
        html_template="letters/email/letter_created.html",
        split_subject=True,
        context=lambda: {
            "target": _letter(actor_is_staff=False),
            "actor": _actor(is_staff=False),
        },
    ),
    EmailCatalogEntry(
        group="Pisma",
        key="letter_created_unactivated",
        title="Nowe pismo w sprawie (konto klienta nieaktywowane)",
        trigger=(
            "Ten sam szablon co wyżej, ale odbiorcą jest klient, którego "
            "konto nie ma jeszcze ustawionego hasła - patrz "
            "letter_send_to_client_unactivated poniżej po wyjaśnienie."
        ),
        sender=_CASE_ADDRESS_SENDER + " (autor pisma)",
        recipient="jak wyżej - tu klient jeszcze bez ustawionego hasła",
        txt_template="letters/email/letter_created.txt",
        html_template="letters/email/letter_created.html",
        split_subject=True,
        context=_unactivated_client_context,
    ),
    EmailCatalogEntry(
        group="Pisma",
        key="letter_updated",
        title="Pismo zaktualizowane",
        trigger=(
            "LetterUpdateView.formset_valid (letters/views/cbv.py) - "
            "wysyłane po edycji dowolnego pisma, także takiego które ma "
            "już status „done” (np. poprawka literówki w odpowiedzi "
            "wcześniej wysłanej do klienta) - wtedy klient też dostaje tę "
            "wiadomość i obowiązuje ten sam dopisek o aktywacji konta co w "
            "letter_send_to_client, zob. wpis niżej."
        ),
        sender=_CASE_ADDRESS_SENDER + " (osoba edytująca pismo)",
        recipient=(
            "personel przypisany do sprawy; klient dodatkowo, jeśli pismo ma "
            "już status „gotowe”"
        ),
        txt_template="letters/email/letter_updated.txt",
        html_template="letters/email/letter_updated.html",
        split_subject=True,
        context=lambda: {
            "target": _letter(actor_is_staff=True),
            "actor": _actor(is_staff=True),
        },
    ),
    EmailCatalogEntry(
        group="Pisma",
        key="letter_updated_unactivated",
        title="Pismo zaktualizowane (konto klienta nieaktywowane)",
        trigger=(
            "Ten sam szablon co wyżej, ale odbiorcą jest klient, którego "
            "konto nie ma jeszcze ustawionego hasła - patrz "
            "letter_send_to_client_unactivated poniżej po wyjaśnienie."
        ),
        sender=_CASE_ADDRESS_SENDER + " (osoba edytująca pismo)",
        recipient="jak wyżej - tu klient jeszcze bez ustawionego hasła",
        txt_template="letters/email/letter_updated.txt",
        html_template="letters/email/letter_updated.html",
        split_subject=True,
        context=_unactivated_client_context,
    ),
    EmailCatalogEntry(
        group="Pisma",
        key="letter_drop_a_note",
        title="Dodano notatkę do sprawy",
        trigger=(
            "LetterCommentForm.save() (letters/forms.py) - wysyłane, gdy "
            "ktoś doda wewnętrzną notatkę."
        ),
        sender=_CASE_ADDRESS_SENDER + " (autor notatki)",
        recipient="wyłącznie personel przypisany do sprawy (nigdy klient)",
        txt_template="letters/email/letter_drop_a_note.txt",
        html_template="letters/email/letter_drop_a_note.html",
        split_subject=True,
        context=lambda: {
            "target": _letter(actor_is_staff=True),
            "actor": _actor(is_staff=True),
        },
    ),
    EmailCatalogEntry(
        group="Pisma",
        key="letter_send_to_client",
        title="Pismo wysłane do klienta",
        trigger=(
            "SendLetterForm.save() (letters/forms.py) - wysyłane do klienta, "
            "gdy pracownik zatwierdzi i wyśle przygotowaną odpowiedź. Jeżeli "
            "konto klienta nie ma jeszcze ustawionego hasła, szablon dokleja "
            "wcześniej dodatkowy link do dokończenia aktywacji konta (blok "
            "_activation_link.html/.txt, współdzielony też przez "
            "letter_created i letter_updated) - zob. wpis niżej."
        ),
        sender=_CASE_ADDRESS_SENDER + " (pracownik wysyłający pismo)",
        recipient="klient oraz cały personel z uprawnieniami do sprawy",
        txt_template="letters/email/letter_send_to_client.txt",
        html_template="letters/email/letter_send_to_client.html",
        split_subject=True,
        context=lambda: {
            "target": _letter(actor_is_staff=True),
            "actor": _actor(is_staff=True),
        },
    ),
    EmailCatalogEntry(
        group="Pisma",
        key="letter_send_to_client_unactivated",
        title="Pismo wysłane do klienta (konto nieaktywowane)",
        trigger=(
            "Ten sam szablon co wyżej, ale odbiorcą jest klient, którego konto "
            "nie ma jeszcze ustawionego hasła (np. utworzone automatycznie z "
            "przychodzącego e-maila, zanim klient dokończył aktywację - zob. "
            "account_activation poniżej). Ponieważ klient nie może się jeszcze "
            "zalogować, przed odnośnikiem do akt sprawy pojawia się dodatkowy "
            "link do dokończenia aktywacji konta (User.get_activation_path())."
        ),
        sender=_CASE_ADDRESS_SENDER + " (pracownik wysyłający pismo)",
        recipient=(
            "klient bez ustawionego hasła oraz cały personel z uprawnieniami "
            "do sprawy"
        ),
        txt_template="letters/email/letter_send_to_client.txt",
        html_template="letters/email/letter_send_to_client.html",
        split_subject=True,
        context=_unactivated_client_context,
    ),
    EmailCatalogEntry(
        group="Pisma",
        key="letter_accepted",
        title="Pismo zaakceptowane",
        trigger=(
            "Szablon zdefiniowany w TemplateMailManager.TEMPLATE_MAP, ale "
            "żaden kod w repozytorium go obecnie nie wysyła."
        ),
        sender="— (martwy kod, zob. Uwaga wyżej)",
        recipient="— (martwy kod, zob. Uwaga wyżej)",
        txt_template="letters/email/letter_accepted.txt",
        html_template="letters/email/letter_accepted.html",
        split_subject=True,
        context=lambda: {
            "target": _letter(actor_is_staff=True),
            "actor": _actor(is_staff=True),
        },
        note=(
            "Martwy kod: nie znaleziono żadnego wywołania "
            "TemplateKey.LETTER_ACCEPTED poza samą mapą szablonów."
        ),
    ),
    EmailCatalogEntry(
        group="Pisma",
        key="letter_refused",
        title="Odrzucona wiadomość e-mail spoza Poradni",
        trigger=(
            "ReceiveEmailView.refuse_letter (letters/views/cbv.py) - wysyłane "
            "do nadawcy, gdy wiadomość przychodząca webhookiem pocztowym nie "
            "była zaadresowana do Poradni (nie pasuje do żadnej znanej sprawy)."
        ),
        sender=_DEFAULT_SENDER,
        recipient="nadawca odrzuconej wiadomości (adres z nagłówka „From:”)",
        txt_template="letters/email/letter_refused.txt",
        html_template="letters/email/letter_refused.html",
        split_subject=True,
        context=lambda: {
            "to": "przypadkowy-adres@example.com",
            "subject": "Wiadomość niezwiązana z Poradnią",
        },
    ),
    # -- Użytkownicy (users) ----------------------------------------------
    EmailCatalogEntry(
        group="Użytkownicy",
        key="account_activation",
        title="Aktywacja konta po zgłoszeniu sprawy e-mailem",
        trigger=(
            "UserManager.send_activation_email (users/models.py), wywoływane z "
            "register_by_email() - wysyłane, gdy nowa sprawa wpłynie od "
            "nieznanego adresu e-mail i zostanie dla niego utworzone konto "
            "bez hasła."
        ),
        sender=_DEFAULT_SENDER,
        recipient="nowo utworzone konto (adres e-mail ze zgłoszenia)",
        txt_template="users/email/account_activation.txt",
        html_template="users/email/account_activation.html",
        split_subject=True,
        context=lambda: {
            "user": Mock("Jan Kowalski"),
            "activation_path": "/uzytkownik/aktywuj/MQ/abc123-token/",
        },
    ),
    EmailCatalogEntry(
        group="Użytkownicy",
        key="existing_case_attempt",
        title="Próba zgłoszenia sprawy na istniejący adres e-mail",
        trigger=(
            "NewCaseCreateView.form_valid (letters/views/cbv.py) - wysyłane do "
            "właściciela konta, gdy ktoś niezalogowany spróbuje zgłosić nową "
            "sprawę używając adresu e-mail już powiązanego z istniejącym "
            "kontem (zamiast ujawniać to zgłaszającemu - patrz "
            "ACCOUNT_PREVENT_ENUMERATION)."
        ),
        sender=_DEFAULT_SENDER,
        recipient=(
            "adres e-mail, na który próbowano zarejestrować nową sprawę "
            "(właściciel istniejącego konta)"
        ),
        txt_template="users/email/existing_case_attempt.txt",
        html_template="users/email/existing_case_attempt.html",
        split_subject=True,
        context=dict,
    ),
    # -- Konto (django-allauth: rejestracja, hasło, e-mail) ---------------
    EmailCatalogEntry(
        group="Konto (allauth)",
        key="email_confirmation",
        title="Potwierdzenie adresu e-mail",
        trigger=(
            "allauth - wysyłane przy rejestracji/dodaniu adresu e-mail "
            "wymagającego potwierdzenia."
        ),
        sender=_ALLAUTH_SENDER,
        recipient="użytkownik potwierdzający adres e-mail",
        txt_template="account/email/email_confirmation_message.txt",
        html_template="account/email/email_confirmation_message.html",
        subject_template="account/email/email_confirmation_subject.txt",
        context=lambda: {
            "user": Mock("Jan Kowalski"),
            "activate_url": (
                "https://poradnia.siecobywatelska.pl/konta/" "potwierdz-email/token123/"
            ),
        },
    ),
    EmailCatalogEntry(
        group="Konto (allauth)",
        key="account_already_exists",
        title="Próba rejestracji na istniejący adres e-mail",
        trigger=(
            "allauth, ACCOUNT_PREVENT_ENUMERATION (domyślnie włączone) - "
            "wysyłane zamiast ujawnienia błędu „konto już istnieje” w "
            "formularzu rejestracji."
        ),
        sender=_ALLAUTH_SENDER,
        recipient="adres e-mail podany w formularzu rejestracji",
        txt_template="account/email/account_already_exists_message.txt",
        html_template="account/email/account_already_exists_message.html",
        subject_template="account/email/account_already_exists_subject.txt",
        context=lambda: {
            "email": "jan.kowalski@example.com",
            "password_reset_url": (
                "https://poradnia.siecobywatelska.pl/konta/haslo/reset/"
            ),
        },
    ),
    EmailCatalogEntry(
        group="Konto (allauth)",
        key="unknown_account",
        title="Próba resetu hasła na nieistniejący adres e-mail",
        trigger=(
            "allauth, ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS (domyślnie włączone) - "
            "wysyłane zamiast ujawnienia, że podany adres nie ma konta, gdy "
            "ktoś poprosi o reset hasła."
        ),
        sender=_ALLAUTH_SENDER,
        recipient="adres e-mail podany przy próbie resetu hasła",
        txt_template="account/email/unknown_account_message.txt",
        html_template="account/email/unknown_account_message.html",
        subject_template="account/email/unknown_account_subject.txt",
        context=lambda: {
            "email": "nieznany@example.com",
            "signup_url": "https://poradnia.siecobywatelska.pl/konta/rejestracja/",
        },
    ),
    EmailCatalogEntry(
        group="Konto (allauth)",
        key="password_reset_key",
        title="Link do zresetowania hasła",
        trigger=(
            "allauth - wysyłane po złożeniu prośby o reset hasła dla "
            "istniejącego konta."
        ),
        sender=_ALLAUTH_SENDER,
        recipient="użytkownik resetujący hasło",
        txt_template="account/email/password_reset_key_message.txt",
        html_template="account/email/password_reset_key_message.html",
        subject_template="account/email/password_reset_key_subject.txt",
        context=lambda: {
            "user": Mock("Jan Kowalski"),
            "password_reset_url": (
                "https://poradnia.siecobywatelska.pl/konta/haslo/reset/key/"
            ),
            "username": "jan.kowalski",
        },
    ),
    EmailCatalogEntry(
        group="Konto (allauth)",
        key="password_changed",
        title="Powiadomienie o zmianie hasła",
        trigger=(
            "allauth, wymaga ACCOUNT_EMAIL_NOTIFICATIONS=True (włączone w tym "
            "projekcie) - wysyłane po zmianie hasła jako powiadomienie "
            "bezpieczeństwa."
        ),
        sender=_ALLAUTH_SENDER,
        recipient="użytkownik, którego hasło zmieniono",
        txt_template="account/email/password_changed_message.txt",
        html_template="account/email/password_changed_message.html",
        subject_template="account/email/password_changed_subject.txt",
        context=lambda: {"user": Mock("Jan Kowalski"), **_notification_meta()},
    ),
    EmailCatalogEntry(
        group="Konto (allauth)",
        key="password_set",
        title="Powiadomienie o ustawieniu hasła",
        trigger=(
            "allauth, wymaga ACCOUNT_EMAIL_NOTIFICATIONS=True - wysyłane, gdy "
            "konto bez hasła (np. utworzone automatycznie ze zgłoszenia "
            "e-mail) ustawi hasło po raz pierwszy."
        ),
        sender=_ALLAUTH_SENDER,
        recipient="użytkownik, który ustawił hasło po raz pierwszy",
        txt_template="account/email/password_set_message.txt",
        html_template="account/email/password_set_message.html",
        subject_template="account/email/password_set_subject.txt",
        context=lambda: {"user": Mock("Jan Kowalski"), **_notification_meta()},
    ),
    EmailCatalogEntry(
        group="Konto (allauth)",
        key="email_changed",
        title="Powiadomienie o zmianie adresu e-mail",
        trigger=(
            "allauth, wymaga ACCOUNT_EMAIL_NOTIFICATIONS=True - wysyłane po "
            "zmianie adresu e-mail konta."
        ),
        sender=_ALLAUTH_SENDER,
        recipient="użytkownik, którego adres e-mail zmieniono",
        txt_template="account/email/email_changed_message.txt",
        html_template="account/email/email_changed_message.html",
        subject_template="account/email/email_changed_subject.txt",
        context=lambda: {
            "user": Mock("Jan Kowalski"),
            "from_email": "stary@example.com",
            "to_email": "nowy@example.com",
            **_notification_meta(),
        },
    ),
    EmailCatalogEntry(
        group="Konto (allauth)",
        key="email_deleted",
        title="Powiadomienie o usunięciu adresu e-mail",
        trigger=(
            "allauth, wymaga ACCOUNT_EMAIL_NOTIFICATIONS=True - wysyłane po "
            "usunięciu dodatkowego adresu e-mail z konta."
        ),
        sender=_ALLAUTH_SENDER,
        recipient="użytkownik, którego dodatkowy adres e-mail usunięto",
        txt_template="account/email/email_deleted_message.txt",
        html_template="account/email/email_deleted_message.html",
        subject_template="account/email/email_deleted_subject.txt",
        context=lambda: {
            "user": Mock("Jan Kowalski"),
            "deleted_email": "stary@example.com",
            **_notification_meta(),
        },
    ),
    # -- Uwierzytelnianie dwuskładnikowe (django-allauth MFA) -------------
    EmailCatalogEntry(
        group="MFA",
        key="totp_activated",
        title="Aktywowano aplikację uwierzytelniającą",
        trigger=(
            "allauth-mfa, wymaga ACCOUNT_EMAIL_NOTIFICATIONS=True - "
            "wysyłane po włączeniu TOTP."
        ),
        sender=_DEFAULT_SENDER + " (allauth-mfa)",
        recipient="użytkownik, który włączył TOTP",
        txt_template="mfa/email/totp_activated_message.txt",
        html_template="mfa/email/totp_activated_message.html",
        subject_template="mfa/email/totp_activated_subject.txt",
        context=lambda: {"user": Mock("Jan Kowalski"), **_notification_meta()},
    ),
    EmailCatalogEntry(
        group="MFA",
        key="totp_deactivated",
        title="Dezaktywowano aplikację uwierzytelniającą",
        trigger=(
            "allauth-mfa, wymaga ACCOUNT_EMAIL_NOTIFICATIONS=True - "
            "wysyłane po wyłączeniu TOTP."
        ),
        sender=_DEFAULT_SENDER + " (allauth-mfa)",
        recipient="użytkownik, który wyłączył TOTP",
        txt_template="mfa/email/totp_deactivated_message.txt",
        html_template="mfa/email/totp_deactivated_message.html",
        subject_template="mfa/email/totp_deactivated_subject.txt",
        context=lambda: {"user": Mock("Jan Kowalski"), **_notification_meta()},
    ),
    EmailCatalogEntry(
        group="MFA",
        key="recovery_codes_generated",
        title="Wygenerowano nowe kody zapasowe",
        trigger=(
            "allauth-mfa, wymaga ACCOUNT_EMAIL_NOTIFICATIONS=True - "
            "wysyłane, gdy użytkownik wygeneruje nowy komplet kodów "
            "zapasowych."
        ),
        sender=_DEFAULT_SENDER + " (allauth-mfa)",
        recipient="użytkownik, który wygenerował nowe kody zapasowe",
        txt_template="mfa/email/recovery_codes_generated_message.txt",
        html_template="mfa/email/recovery_codes_generated_message.html",
        subject_template="mfa/email/recovery_codes_generated_subject.txt",
        context=lambda: {"user": Mock("Jan Kowalski"), **_notification_meta()},
    ),
    # -- Konta zewnętrzne (django-allauth socialaccount) ------------------
    EmailCatalogEntry(
        group="Konta zewnętrzne",
        key="account_connected",
        title="Połączono konto zewnętrzne (np. Google)",
        trigger=(
            "allauth-socialaccount, wymaga ACCOUNT_EMAIL_NOTIFICATIONS=True "
            "- wysyłane po połączeniu konta z dostawcą logowania "
            "społecznościowego."
        ),
        sender=_DEFAULT_SENDER + " (allauth-socialaccount)",
        recipient="użytkownik, który połączył konto zewnętrzne",
        txt_template="socialaccount/email/account_connected_message.txt",
        html_template="socialaccount/email/account_connected_message.html",
        subject_template="socialaccount/email/account_connected_subject.txt",
        context=lambda: {
            "user": Mock("Jan Kowalski"),
            "provider": "Google",
            **_notification_meta(),
        },
    ),
    EmailCatalogEntry(
        group="Konta zewnętrzne",
        key="account_disconnected",
        title="Odłączono konto zewnętrzne (np. Google)",
        trigger=(
            "allauth-socialaccount, wymaga ACCOUNT_EMAIL_NOTIFICATIONS=True "
            "- wysyłane po odłączeniu konta dostawcy logowania "
            "społecznościowego."
        ),
        sender=_DEFAULT_SENDER + " (allauth-socialaccount)",
        recipient="użytkownik, który odłączył konto zewnętrzne",
        txt_template="socialaccount/email/account_disconnected_message.txt",
        html_template="socialaccount/email/account_disconnected_message.html",
        subject_template="socialaccount/email/account_disconnected_subject.txt",
        context=lambda: {
            "user": Mock("Jan Kowalski"),
            "provider": "Google",
            **_notification_meta(),
        },
    ),
    # -- Inne ---------------------------------------------------------------
    EmailCatalogEntry(
        group="Inne",
        key="feedback_manager_notification",
        title="Powiadomienie zespołu o nowej opinii (feedback)",
        trigger=(
            "Sygnał post_save modelu Feedback (tasty_feedback/models.py: "
            "notify_manager) - wysyłane do adresów z ustawienia MANAGERS, gdy "
            "użytkownik zgłosi opinię/błąd przez widget feedbacku."
        ),
        sender=_SERVER_EMAIL_SENDER,
        recipient=_MANAGERS_RECIPIENT,
        note=(
            "Ten e-mail nie używa żadnego szablonu Django - "
            "mail_managers_replyable() (tasty_feedback/utils.py) buduje temat "
            "i treść z gołych łańcuchów znaków w kodzie. Nie jest kierowany "
            "do klientów, więc celowo nie ma stopki z _email_signature."
        ),
        raw_example=(
            "Temat: New feedback - 2026-07-24 12:00:00\n\n"
            'Coś nie działa na stronie sprawy, przycisk "Wyślij" jest '
            "wyszarzony.\n"
            "URL:https://poradnia.siecobywatelska.pl/sprawy/123/"
        ),
    ),
]
