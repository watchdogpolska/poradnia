"""Hardcoded catalog of every outbound e-mail template in the app, used by
the staff-only preview page at /admin/email-catalog/ (see views.py).

This list is maintained by hand. If you add, rename or remove an e-mail
template anywhere in the app, update the matching entry here too.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


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
    txt_template: Optional[str] = None
    html_template: Optional[str] = None
    subject_template: Optional[str] = None  # allauth-style: subject rendered separately
    split_subject: bool = (
        False  # TemplateMailManager-style: subject = first line of txt
    )
    context: Callable[[], dict] = field(default=dict)
    note: Optional[str] = None
    raw_example: Optional[str] = None  # for entries with no Django template at all


def _case():
    return Mock(
        "#123 Wniosek o dostęp do informacji publicznej",
        client=Mock("Jan Kowalski"),
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


def _letter(actor_is_staff=False):
    if actor_is_staff:
        return Mock(
            "Odpowiedź na pytanie",
            name="Odpowiedź na pytanie",
            text=(
                "Szanowni Państwo,\n\nw odpowiedzi na pytanie uprzejmie informujemy..."
            ),
            created_by=Mock("Anna Nowak (Poradnia)"),
            case=_case(),
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
        case=_case(),
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
            "LetterFromMailView / NewCaseCreateView (letters/views/cbv.py) - "
            "wysyłane, gdy w sprawie pojawi się nowe pismo (np. e-mail od "
            "klienta przychodzący przez IMAP/webhook)."
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
        key="letter_updated",
        title="Pismo zaktualizowane",
        trigger=(
            "LetterUpdateForm.save() (letters/views/cbv.py) - wysyłane po "
            "edycji pisma."
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
        key="letter_drop_a_note",
        title="Dodano notatkę do sprawy",
        trigger=(
            "LetterCommentForm.save() (letters/forms.py) - wysyłane, gdy "
            "ktoś doda wewnętrzną notatkę."
        ),
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
            "LetterSendToClientForm.save() (letters/forms.py) - wysyłane do "
            "klienta, gdy pracownik zatwierdzi i wyśle przygotowaną odpowiedź."
        ),
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
        key="letter_accepted",
        title="Pismo zaakceptowane",
        trigger=(
            "Szablon zdefiniowany w TemplateMailManager.TEMPLATE_MAP, ale "
            "żaden kod w repozytorium go obecnie nie wysyła."
        ),
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
            "LetterFromMailView.refuse_letter (letters/views/cbv.py) - wysyłane "
            "do nadawcy, gdy wiadomość przychodząca webhookiem pocztowym nie "
            "była zaadresowana do Poradni (nie pasuje do żadnej znanej sprawy)."
        ),
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
