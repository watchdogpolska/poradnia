// The URL x role sample used by both baseline_capture.js and (later)
// axe_run.js / validate_html.js. Mirrors logs/wcag/HANDOFF.md section 6.2.
// pks below are stable because seed_a11y.py resets MySQL AUTO_INCREMENT on
// every --reset (see reset_autoincrement()) — re-run the seed and these
// still point at the right objects. If the seed script's creation order
// changes, re-derive these ids (see logs/wcag/README.md).
//
// Covers every named flow in HANDOFF §6.2 except session-expiry (2.2.1),
// which is a multi-request behavioral check, not a single page to
// screenshot -- that's exercised procedurally during §6.4, not here. The
// "~10% of remaining pages at random" draw is approximated by a deliberate
// handful of previously-untouched page/component types (users:list,
// letters:list, events:table, admin changelists, teryt) rather than a true
// RNG draw over all 426 show_urls lines (most of which are repetitive
// per-model admin CRUD) -- see audit/sample.md for the full rationale.

const SEEDED = {
  case: {
    thread1: 1, // free, 1 letter
    thread5: 2, // moderated, 5 letters (every genre/status)
    thread25: 3, // assigned, 25 letters, has CourtCase + "today" Event
    closed: 4,
    moderated: 5,
    maxlen: 6,
    diacritics: 7,
    xss: 8,
    other_client_longname: 7, // belongs to a11y_client_longname, not client_active
  },
  letter: {
    ai_message_in_thread25: 10, // genre=ai_message, status=staff
  },
  attachment: {
    text_modal_target: 3, // sample.txt on a letter in case 3 (thread25)
  },
  advice: { linked_to_thread5: 1 },
  key: { client_active: 1 },
  feedback: { client_active: 1 },
  // past -> case2 (thread5), today -> case3 (thread25), future -> case4 (closed)
  event: { past: 1, today: 2, future: 3 },
};

// Each entry: {id, role, path, note, interactions?}
// interactions (optional) describe extra states captured from the same page
// load, each becoming its own baseline/<role>/<id>__<interactionId>.html +
// screenshots. See baseline_capture.js for the supported interaction kinds.
const SAMPLE = [
  // --- Anonymous -----------------------------------------------------
  { id: "home", role: "anon", path: "/", note: "Home page" },
  { id: "terms", role: "anon", path: "/strony/regulamin-poradnictwa/", note: "Terms" },
  { id: "privacy", role: "anon", path: "/strony/polityka-prywatnosci/", note: "Privacy policy" },
  { id: "signup", role: "anon", path: "/konta/signup/", note: "Signup form" },
  { id: "login", role: "anon", path: "/konta/login/", note: "Login form" },
  { id: "password_reset", role: "anon", path: "/konta/password/reset/", note: "Password reset request" },
  // Anonymous hitting any case URL redirects to login (200 after redirect),
  // so the 404 check needs an authenticated role to actually reach the
  // "does this case exist" check inside the view. Confirmed live: 404.
  { id: "error_404", role: "staff_admin", path: "/sprawy/sprawa-999999/", note: "Nonexistent case -> 404", allowStatus: [404] },
  { id: "teryt_list", role: "anon", path: "/teryt/", note: "Administrative-unit list (anonymous-reachable)" },

  // --- Client (a11y_client_active) ------------------------------------
  { id: "client_cases_list", role: "client_active", path: "/sprawy/", note: "Client's case list" },
  {
    id: "client_case_detail_thread1",
    role: "client_active",
    path: `/sprawy/sprawa-${SEEDED.case.thread1}/`,
    note: "Case detail, 1-message thread, unassigned (free)",
  },
  {
    id: "client_case_detail_thread5",
    role: "client_active",
    path: `/sprawy/sprawa-${SEEDED.case.thread5}/`,
    note: "Case detail, 5-message thread, reply form",
    interactions: ["attachment_text_modal"],
  },
  {
    id: "client_case_forbidden",
    role: "client_active",
    path: `/sprawy/sprawa-${SEEDED.case.other_client_longname}/`,
    note: "Case belonging to a different client -> expect 403",
    allowStatus: [403],
  },
  { id: "client_new_case_form", role: "client_active", path: "/listy/", note: "New case form (GET)" },
  { id: "client_profile", role: "client_active", path: "/uzytkownik/~profil/", note: "Profile edit" },
  { id: "client_password_change", role: "client_active", path: "/konta/password/change/", note: "Password change" },
  {
    id: "client_own_detail",
    role: "client_active",
    path: "/uzytkownik/a11y_client_active/",
    note: "Own user-detail page (users:detail, always allowed for self)",
  },
  // Despite HANDOFF §6.2 listing "API keys" under the client flow,
  // keys:list is gated by SuperuserPermissionMixin (confirmed live: a11y_client_active
  // gets 403 here) -- it is not actually a client-facing page today. Captured
  // under superuser instead; flagged in the Checkpoint 2 report.
  { id: "superuser_api_keys", role: "superuser", path: "/uzytkownik/klucze", note: "API keys list (superuser-only, not client-facing)" },

  // --- Client edge cases (empty / long name) --------------------------
  { id: "client_empty_cases_list", role: "client_empty", path: "/sprawy/", note: "Client with zero cases: empty state" },
  {
    id: "client_longname_case_detail",
    role: "client_longname",
    path: `/sprawy/sprawa-${SEEDED.case.diacritics}/`,
    note: "Long diacritic name, diacritic case subject",
  },

  // --- Staff (wsparcie) ------------------------------------------------
  {
    id: "staff_dashboard",
    role: "staff_wsparcie",
    path: "/dashboard/",
    note: "Staff dashboard",
    interactions: ["navsearch_modal_open"],
  },
  {
    id: "staff_cases_list",
    role: "staff_wsparcie",
    path: "/sprawy/",
    note: "Staff case list, plain Django pagination+filter (cases:list / case_filter.html)",
    interactions: ["dal_dropdown_open"],
  },
  // cases:table (case_table.html) is the *separate* page hosting the real
  // #datatable_cases DataTables instance -- cases:list above is a plain
  // paginated FilterView and has no DataTables markup at all.
  {
    id: "staff_cases_datatable",
    role: "staff_wsparcie",
    path: "/sprawy/table/",
    note: "Staff case DataTable (65 rows, server-side)",
    interactions: ["datatable_sort_name", "datatable_page_length_25", "datatable_filter"],
  },
  { id: "staff_events_calendar", role: "staff_wsparcie", path: "/wydarzenia/", note: "Events calendar" },
  { id: "staff_advices_list", role: "staff_wsparcie", path: "/porady/", note: "Advices list" },
  {
    id: "staff_advice_detail",
    role: "staff_wsparcie",
    path: `/porady/${SEEDED.advice.linked_to_thread5}`,
    note: "Advice detail, areas+issues",
  },
  // tasty_feedback:list requires the Django model permission
  // tasty_feedback.view_feedback directly, which staff_wsparcie does not
  // have (confirmed live: 403) -- only staff_admin is granted it in
  // seed_a11y.py.
  { id: "staff_feedback_list", role: "staff_admin", path: "/uwagi/", note: "tasty_feedback list" },
  { id: "staff_navsearch", role: "staff_wsparcie", path: "/navsearch/?q=spor", note: "navsearch autocomplete (JSON)", isJson: true },
  { id: "staff_letters_list", role: "staff_wsparcie", path: "/listy/rejestr", note: "Letters register (letters:list)" },
  { id: "staff_users_list", role: "staff_wsparcie", path: "/uzytkownik/", note: "Staff user list (users:list)" },
  { id: "staff_events_table", role: "staff_wsparcie", path: "/wydarzenia/table/", note: "Events DataTable (events:table)" },
  {
    // thread1 (case1) is unassigned -- staff_wsparcie has no permission on
    // it at all, confirmed live (403). Use thread5, where the 'wsparcie'
    // group (which includes can_add_record) was actually granted.
    id: "staff_event_add_form",
    role: "staff_wsparcie",
    path: `/wydarzenia/sprawa-${SEEDED.case.thread5}/`,
    note: "New-event form (events:add)",
  },
  {
    id: "staff_event_edit_form",
    role: "staff_wsparcie",
    path: `/wydarzenia/wydarzenie-${SEEDED.event.past}`,
    note: "Edit-event form (events:edit), existing event in thread5",
  },
  { id: "staff_advice_create_form", role: "staff_wsparcie", path: "/porady/nowa/", note: "New-advice form (advicer:create)" },
  {
    // No trailing slash -- the route is /sprawy_sadowe/~create-<pk> (confirmed
    // via show_urls), not .../~create-<pk>/.
    id: "staff_judgement_create_form",
    role: "staff_wsparcie",
    path: `/sprawy_sadowe/~create-${SEEDED.case.thread5}`,
    note: "New court-case form (judgements:create), on a case with no CourtCase yet",
  },
  {
    // cases:edit needs cases.can_change_case, which only the 'admin' group
    // grants (PERM_INITIAL: 'wsparcie' doesn't include it) -- confirmed live
    // (403 as staff_wsparcie on any case). thread25 is where staff_admin
    // actually holds the 'admin' group.
    id: "staff_case_edit_form",
    role: "staff_admin",
    path: `/sprawy/sprawa-${SEEDED.case.thread25}/edytuj/`,
    note: "Case edit form (cases:edit)",
  },
  {
    // Same story: cases:close needs can_close_case, 'admin'-group only.
    id: "staff_case_close_form",
    role: "staff_admin",
    path: `/sprawy/sprawa-${SEEDED.case.thread25}/zamknij/`,
    note: "Case close confirmation form (cases:close), never submitted",
  },

  // --- Staff (admin group) --------------------------------------------
  { id: "admin_staff_dashboard", role: "staff_admin", path: "/dashboard/", note: "Staff dashboard (admin group)" },
  {
    id: "admin_staff_case_detail_thread25",
    role: "staff_admin",
    path: `/sprawy/sprawa-${SEEDED.case.thread25}/`,
    note: "25-message thread, CourtCase + event, attachments, AI letters",
    interactions: ["ai_reject_modal_open"],
  },
  // --- Superuser / Django admin ----------------------------------------
  // closed/xss/maxlen cases below were never granted to staff_admin by the
  // seed script (only thread25 got the 'admin' group) -- CaseDetailView
  // enforces per-object cases.can_view via guardian, so staff_admin gets a
  // real 403 on them (confirmed live). Superusers bypass per-object
  // permission checks entirely, which is the right role for "just inspect
  // this content" rendering/escaping checks anyway.
  { id: "superuser_admin_index", role: "superuser", path: "/admin/", note: "Django admin index" },
  {
    id: "superuser_case_detail_closed",
    role: "superuser",
    path: `/sprawy/sprawa-${SEEDED.case.closed}/`,
    note: "Closed case",
  },
  {
    id: "superuser_case_detail_xss",
    role: "superuser",
    path: `/sprawy/sprawa-${SEEDED.case.xss}/`,
    note: "Subject containing <b>test</b> -> escaping check",
  },
  {
    id: "superuser_case_detail_maxlen",
    role: "superuser",
    path: `/sprawy/sprawa-${SEEDED.case.maxlen}/`,
    note: "NAME_MAX_LENGTH (250 char) subject",
  },
  {
    id: "superuser_admin_case_delete_confirm",
    role: "superuser",
    path: `/admin/cases/case/${SEEDED.case.xss}/delete/`,
    note: "Admin delete-case confirm page (GET only, never submitted)",
  },
  { id: "superuser_admin_case_changelist", role: "superuser", path: "/admin/cases/case/", note: "Django admin: Case changelist" },
  { id: "superuser_admin_letter_changelist", role: "superuser", path: "/admin/letters/letter/", note: "Django admin: Letter changelist (GuardedModelAdmin)" },
];

module.exports = { SAMPLE, SEEDED };
