// Programmatic login helpers shared by baseline_capture.js, baseline_diff.js,
// axe_run.js and validate_html.js. Logs in via the real allauth login form
// (same field names/CSRF flow a human uses), not a backdoor, so the sample
// captures the real auth path too.
const { request } = require("playwright");

const BASE_URL = process.env.A11Y_BASE_URL || "http://localhost:8000";

// Usernames from logs/wcag/scripts/seed_a11y.py. Keep in sync.
const USERNAMES = {
  anon: null,
  client_active: "a11y_client_active",
  client_empty: "a11y_client_empty",
  client_longname: "a11y_client_longname",
  staff_wsparcie: "a11y_staff_wsparcie",
  staff_admin: "a11y_staff_admin",
  staff_obserwator: "a11y_staff_obserwator",
  superuser: "a11y_superuser",
};

function getSeedPassword() {
  const password = process.env.A11Y_SEED_PASSWORD;
  if (!password) {
    throw new Error("A11Y_SEED_PASSWORD env var is required (not printed anywhere).");
  }
  return password;
}

function uiModeCookie(mode) {
  const url = new URL(BASE_URL);
  return {
    name: "ui_mode",
    value: mode,
    domain: url.hostname,
    path: "/",
    expires: Math.floor(Date.now() / 1000) + 86400,
    httpOnly: false,
    secure: false,
    sameSite: "Lax",
  };
}

// mode: "normal" (default) or "wcag" - sets the poradnia.utils.ui_mode
// cookie (see poradnia/utils/middleware.py) so captures/tests can request
// either UI mode without going through the switch control itself.
async function loginStorageState(role, mode = "normal") {
  if (role === "anon" || !USERNAMES[role]) {
    // No session to establish, but WCAG-mode anon captures still need the
    // cookie set - return a bare storage state rather than null so callers
    // get consistent behavior regardless of mode.
    return mode === "wcag" ? { cookies: [uiModeCookie(mode)], origins: [] } : null;
  }
  const username = USERNAMES[role];
  const password = getSeedPassword();
  const context = await request.newContext({ baseURL: BASE_URL });
  try {
    const loginPage = await context.get("/konta/login/");
    const html = await loginPage.text();
    const csrfMatch = html.match(/name="csrfmiddlewaretoken" value="([^"]+)"/);
    if (!csrfMatch) {
      throw new Error("Could not find CSRF token on the login page.");
    }
    const resp = await context.post("/konta/login/", {
      form: { login: username, password, csrfmiddlewaretoken: csrfMatch[1] },
      headers: { Referer: `${BASE_URL}/konta/login/` },
    });
    if (resp.status() >= 400) {
      throw new Error(`Login POST failed for role=${role}: HTTP ${resp.status()}`);
    }
    const state = await context.storageState();
    const hasSession = state.cookies.some((c) => c.name === "sessionid");
    if (!hasSession) {
      throw new Error(
        `Login did not establish a session for role=${role} (bad credentials or form changed?)`
      );
    }
    // Suppress the "alternative donate popup" (poradnia/static/js/donate_popup_alternative.js)
    // the same way a returning visitor who already dismissed it would -- it's a
    // full-page overlay that intercepts clicks on everything underneath, which
    // would otherwise block every interaction capture for non-staff roles.
    const url = new URL(BASE_URL);
    state.cookies.push({
      name: "altPopupShown",
      value: "true",
      domain: url.hostname,
      path: "/",
      expires: Math.floor(Date.now() / 1000) + 86400,
      httpOnly: false,
      secure: false,
      sameSite: "Lax",
    });
    if (mode === "wcag") {
      state.cookies.push(uiModeCookie(mode));
    }
    return state;
  } finally {
    await context.dispose();
  }
}

module.exports = { BASE_URL, USERNAMES, loginStorageState };
