"""Hardcoded catalog of every django.contrib.messages notification raised by
the app, used by the staff-only preview page at /admin/messages-catalog/
(see poradnia/utils/views.py).

This list is maintained by hand. If you add, rename or remove a
messages.success/error/warning/info call (or a success_message /
get_success_message / get_form_valid_message override) anywhere in the app,
update the matching entry here too.

Each entry renders its example through the *real* gettext() call the source
code makes, so the preview picks up the actual active-language translation
(including any translation bugs) instead of a hand-typed guess.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional

from django.utils.translation import gettext

_CASE = "#123 Wniosek o dostęp do informacji publicznej"
_KEY = "Klucz do panelu klienta"


@dataclass
class MessageCatalogEntry:
    group: str
    key: str
    title: str
    trigger: str
    level: str  # django.contrib.messages default tag: debug/info/success/warning/error
    translated: bool = True  # False if the source never wraps the text in _()
    msgid: Optional[str] = None  # exact string literal passed to _() / gettext()
    render: Callable[[str], str] = field(default=lambda text: text)
    build: Optional[Callable[[], str]] = None  # escape hatch for multi-fragment text
    note: Optional[str] = None


CATALOG = [
    # -- Sprawy (cases) ---------------------------------------------------
    MessageCatalogEntry(
        group="Sprawy",
        key="case_updated",
        title="Sprawa zaktualizowana",
        trigger="CaseUpdateView.form_valid (cases/views/cases.py).",
        level="success",
        msgid='Successful updated "%(object)s".',
        render=lambda t: t % {"object": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_closed",
        title="Sprawa zamknięta",
        trigger="CaseCloseView.form_valid (cases/views/cases.py).",
        level="success",
        msgid='Successfully closed "%(object)s".',
        render=lambda t: t % {"object": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_merged",
        title="Sprawy scalone",
        trigger="CaseMergeView.form_valid (cases/views/cases.py).",
        level="success",
        msgid='Successfully merged "%(object)s".',
        render=lambda t: t % {"object": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_article_search_started",
        title="Rozpoczęto wyszukiwanie artykułów (wyszukiwanie bezpośrednie)",
        trigger=(
            "CaseSearchArticlesView.post, direct_search=True (cases/views/cases.py)."
        ),
        level="success",
        msgid='Article search started for "%(object)s".',
        render=lambda t: t % {"object": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_article_classification_started",
        title="Rozpoczęto klasyfikację i wyszukiwanie artykułów",
        trigger=(
            "CaseSearchArticlesView.post, direct_search=False "
            "(cases/views/cases.py)."
        ),
        level="success",
        msgid='Article classification and search started for "%(object)s".',
        render=lambda t: t % {"object": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_article_search_failed",
        title="Nie udało się wyszukać artykułów",
        trigger=(
            "CaseSearchArticlesView.post, gdy search_articles_for_case() "
            "zwróci False."
        ),
        level="error",
        msgid='Article search request failed for "%(object)s". Please try again later.',
        render=lambda t: t % {"object": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_ai_tagging_started",
        title="Rozpoczęto tagowanie AI",
        trigger="CaseRequestAiTagsView.post (cases/views/cases.py).",
        level="success",
        msgid='AI tagging started for "%(object)s".',
        render=lambda t: t % {"object": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_ai_tagging_failed",
        title="Nie udało się rozpocząć tagowania AI",
        trigger=(
            "CaseRequestAiTagsView.post, gdy request_ai_tags_for_case() "
            "zwróci False."
        ),
        level="error",
        msgid='AI tagging request failed for "%(object)s". Please try again later.',
        render=lambda t: t % {"object": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_permission_granted",
        title="Nadano uprawnienia do sprawy",
        trigger="UserPermissionCreateView.form_valid (cases/views/permissions.py).",
        level="success",
        msgid="Success granted permission of %(user)s to %(case)s",
        render=lambda t: t % {"user": "Jan Kowalski", "case": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_permission_updated",
        title="Zaktualizowano uprawnienia użytkownika do sprawy",
        trigger=(
            "UserPermissionUpdateView.get_form_valid_message "
            "(cases/views/permissions.py)."
        ),
        level="success",
        msgid="Updated permission %(user)s to %(case)s!",
        render=lambda t: t % {"user": "Jan Kowalski", "case": _CASE},
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_group_permission_granted",
        title="Nadano uprawnienia grupy do sprawy",
        trigger=(
            "CaseGroupPermissionView.get_form_valid_message "
            "(cases/views/permissions.py)."
        ),
        level="success",
        msgid="{user} granted permissions from {group}!",
        render=lambda t: t.format(user="Jan Kowalski", group="Opiekun sprawy"),
    ),
    MessageCatalogEntry(
        group="Sprawy",
        key="case_permission_removed",
        title="Usunięto uprawnienia użytkownika do sprawy",
        trigger=(
            "UserPermissionRemoveView.get_success_message "
            "(cases/views/permissions.py)."
        ),
        level="success",
        msgid='Removed all permission of "{user}" in case "{case}"',
        render=lambda t: t.format(user="Jan Kowalski", case=_CASE),
    ),
    # -- Pisma (letters) ----------------------------------------------------
    MessageCatalogEntry(
        group="Pisma",
        key="anonymous_case_submitted",
        title="Zgłoszono sprawę anonimowo",
        trigger=(
            "NewCaseCreateView.form_valid oraz .formset_valid "
            "(letters/views/cbv.py) - ten sam ogólny komunikat jest pokazywany "
            "zarówno przy zwykłym anonimowym zgłoszeniu, jak i przy próbie "
            "zgłoszenia na adres już powiązany z istniejącym kontem (celowo "
            "identyczny, patrz ACCOUNT_PREVENT_ENUMERATION)."
        ),
        level="success",
        msgid=(
            "Thank you for submitting your case. Please check your e-mail for "
            "further instructions on how to proceed."
        ),
    ),
    MessageCatalogEntry(
        group="Pisma",
        key="case_created_logged_in",
        title="Utworzono nową sprawę (zalogowany użytkownik)",
        trigger="NewCaseCreateView.formset_valid (letters/views/cbv.py).",
        level="success",
        msgid="Case about {object} created!",
        render=lambda t: t.format(object="Wniosek o dostęp do informacji publicznej"),
    ),
    MessageCatalogEntry(
        group="Pisma",
        key="letter_created",
        title="Dodano nowe pismo",
        trigger="letters.views.fbv.add() (letters/views/fbv.py).",
        level="success",
        msgid="Letter %(object)s created!",
        render=lambda t: t % {"object": "Odpowiedź na pytanie"},
    ),
    MessageCatalogEntry(
        group="Pisma",
        key="letter_send_twice_blocked",
        title="Próba ponownego wysłania pisma",
        trigger=(
            "letters.views.fbv.send(), gdy pismo ma już status „wysłane” "
            "(letters/views/fbv.py)."
        ),
        level="warning",
        msgid="You can not send one letter twice.",
    ),
    MessageCatalogEntry(
        group="Pisma",
        key="letter_sent",
        title="Wysłano pismo do klienta",
        trigger="letters.views.fbv.send() (letters/views/fbv.py).",
        level="success",
        msgid="Letter %(object)s send!",
        render=lambda t: t % {"object": "Odpowiedź na pytanie"},
    ),
    MessageCatalogEntry(
        group="Pisma",
        key="formset_mixin_default_created",
        title="Domyślny komunikat po zapisaniu formularza z załącznikami",
        trigger=(
            "FormSetMixin.formset_valid, domyślna get_formset_valid_message() "
            "(utils/crispy_forms.py) - używana przez LetterUpdateView, która nie "
            "nadpisuje tego komunikatu."
        ),
        level="success",
        msgid="{0} created!",
        render=lambda t: t.format("Odpowiedź na pytanie"),
        note=(
            "LetterUpdateView to widok EDYCJI pisma, ale odziedziczony komunikat "
            "mówi „created!” (utworzono), bo nikt go tam nie nadpisał - myląca "
            "treść, nie literówka w tym podglądzie."
        ),
    ),
    # -- Wydarzenia (events) --------------------------------------------------
    MessageCatalogEntry(
        group="Wydarzenia",
        key="event_created",
        title="Dodano nowe wydarzenie",
        trigger="EventCreateView.get_form_valid_message (events/views.py).",
        level="success",
        msgid="Success added new event %(event)s",
        render=lambda t: t % {"event": "Termin odpowiedzi na wniosek"},
    ),
    MessageCatalogEntry(
        group="Wydarzenia",
        key="event_updated",
        title="Zaktualizowano wydarzenie",
        trigger="EventUpdateView.get_form_valid_message (events/views.py).",
        level="success",
        msgid="Success updated event %(event)s",
        render=lambda t: t % {"event": "Termin odpowiedzi na wniosek"},
    ),
    # -- Sprawy sądowe (judgements) -------------------------------------------
    MessageCatalogEntry(
        group="Sprawy sądowe",
        key="courtcase_created",
        title="Dodano sprawę sądową",
        trigger="CourtCaseCreateView.get_form_valid_message (judgements/views.py).",
        level="success",
        msgid="{0} created!",
        render=lambda t: t.format("II SA/Wa 123/26"),
        note=(
            "Martwy kod: CourtCaseCreateView nie dziedziczy z "
            "FormValidMessageMixin, więc get_form_valid_message() jest "
            "zdefiniowana, ale nigdy nie jest wywoływana - w praktyce po "
            "dodaniu sprawy sądowej nie pojawia się żaden komunikat."
        ),
    ),
    MessageCatalogEntry(
        group="Sprawy sądowe",
        key="courtcase_updated",
        title="Zaktualizowano sprawę sądową",
        trigger="CourtCaseUpdateView.get_form_valid_message (judgements/views.py).",
        level="success",
        msgid="{0} updated!",
        render=lambda t: t.format("II SA/Wa 123/26"),
    ),
    MessageCatalogEntry(
        group="Sprawy sądowe",
        key="courtcase_deleted",
        title="Usunięto sprawę sądową",
        trigger="CourtCaseDeleteView.get_success_message (judgements/views.py).",
        level="success",
        msgid="{0} deleted!",
        render=lambda t: t.format("II SA/Wa 123/26"),
    ),
    # -- Porady (advicer) ------------------------------------------------------
    MessageCatalogEntry(
        group="Porady",
        key="advice_deleted",
        title="Usunięto poradę",
        trigger=(
            "AdviceDelete.success_message, przez "
            "utils.action_views.ActionMessageMixin (advicer/views.py)."
        ),
        level="success",
        msgid="{subject} deleted!",
        render=lambda t: t.format(
            subject="Porada w sprawie o dostęp do informacji publicznej"
        ),
    ),
    # -- Użytkownicy (users) -----------------------------------------------
    MessageCatalogEntry(
        group="Użytkownicy",
        key="account_activated",
        title="Aktywowano konto i ustawiono hasło",
        trigger="AccountActivationView.form_valid (users/views.py).",
        level="success",
        msgid="Your account is now active and your password is set.",
    ),
    MessageCatalogEntry(
        group="Użytkownicy",
        key="user_deassigned",
        title="Wycofano przypisania użytkownika do spraw",
        trigger="UserDeassignView.get_success_message (users/views.py).",
        level="success",
        msgid="{object} deassigned from {count} cases",
        render=lambda t: t.format(object="Jan Kowalski", count=3),
        note=(
            "Klasowy atrybut success_message = _('{subject} deassigned') jest "
            "martwy - get_success_message() jest nadpisane i faktycznie "
            "wysyłany jest tekst pokazany w podglądzie."
        ),
    ),
    # -- Klucze (keys) -------------------------------------------------------
    MessageCatalogEntry(
        group="Klucze",
        key="key_downloaded",
        title="Pobrano klucz",
        trigger="KeyDetailView.get_object (keys/views.py).",
        level="success",
        translated=False,
        msgid="{object} downloaded!",
        render=lambda t: t.format(object=_KEY),
        note=(
            "Ten komunikat nie jest owinięty w _() - zawsze wyświetla się po "
            "angielsku."
        ),
    ),
    MessageCatalogEntry(
        group="Klucze",
        key="key_deleted",
        title="Usunięto klucz",
        trigger=(
            "KeyDeleteView.get_success_message, przez "
            "utils.action_views.DeleteMessageMixin (keys/views.py)."
        ),
        level="success",
        msgid="{object} deleted!",
        render=lambda t: t.format(object=_KEY),
    ),
    # -- Uwagi (tasty_feedback) ----------------------------------------------
    MessageCatalogEntry(
        group="Uwagi",
        key="feedback_saved",
        title="Zapisano zgłoszoną uwagę",
        trigger=(
            "FeedbackCreateView.get_form_valid_message, przez "
            "utils.mixins.FormValidMessageMixin (tasty_feedback/views.py)."
        ),
        level="success",
        msgid="Feedback saved.",
    ),
    MessageCatalogEntry(
        group="Uwagi",
        key="feedback_status_switched",
        title="Zmieniono status uwagi (rozwiązana/nierozwiązana)",
        trigger="FeedbackStatusView.delete (tasty_feedback/views.py).",
        level="success",
        msgid="%s updated",
        render=lambda t: t % ("Coś nie działa na stronie sprawy",),
    ),
    # -- Panel administracyjny (Django admin) --------------------------------
    MessageCatalogEntry(
        group="Panel administracyjny",
        key="admin_force_password_change",
        title="Wymuszono zmianę hasła przy następnym logowaniu (akcja administracyjna)",
        trigger=(
            "UserAdmin.force_password_change, akcja listy użytkowników "
            "(users/admin.py)."
        ),
        level="success",
        msgid="Marked %(updated)s user(s) to change password on next login.",
        render=lambda t: t % {"updated": 7},
    ),
    MessageCatalogEntry(
        group="Panel administracyjny",
        key="admin_users_excluded_from_delete",
        title="Część zaznaczonych użytkowników pominięta przy masowym usuwaniu",
        trigger=(
            "UserAdmin.response_action, przechwycona akcja delete_selected, "
            "gdy wśród zaznaczonych są użytkownicy ze sprawami i/lub pismami "
            "(users/admin.py)."
        ),
        level="info",
        build=lambda: (
            gettext("Users with cases can be deleted with user form only: ")
            + "jan.kowalski, anna.nowak"
            + "\n \n"
            + gettext("Users with letters can be deleted with user form only: ")
            + "piotr.zielinski"
        ),
        note="message_user() bez podanego poziomu domyślnie używa poziomu INFO.",
    ),
    MessageCatalogEntry(
        group="Panel administracyjny",
        key="admin_no_users_to_delete",
        title="Brak użytkowników do usunięcia (po wykluczeniach)",
        trigger=(
            "UserAdmin.response_action, gdy wszyscy zaznaczeni użytkownicy "
            "zostali wykluczeni z masowego usuwania (users/admin.py)."
        ),
        level="info",
        msgid="No users to delete.",
    ),
]
