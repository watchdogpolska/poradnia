// Shared capture routine used by baseline_capture.js (writes to baseline/)
// and baseline_diff.js (writes to a throwaway tmp dir, then diffs against
// baseline/). See logs/wcag/HANDOFF.md section 5.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const { BASE_URL, loginStorageState } = require("./auth");
const { normalizeHtml } = require("./normalize");
const { SAMPLE } = require("../sample");

const VIEWPORTS = {
  desktop: { width: 1920, height: 1080 },
  mobile: { width: 375, height: 812 },
};

const DISABLE_ANIMATIONS_CSS = `
  *, *::before, *::after {
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
    caret-color: transparent !important;
    scroll-behavior: auto !important;
  }
`;

// Every condition here is raced against an in-browser setTimeout, not just
// wrapped in a .catch() on the Playwright side: page.evaluate() has no
// timeout of its own, so a promise that never settles (document.fonts.ready
// hung indefinitely on at least one page, confirmed live -- a ~30s stall
// that wasn't any of the other waits) blocks forever regardless of any
// .catch(). Capping with Promise.race *inside* the evaluated function
// guarantees evaluate() itself always returns.
const STABLE_WAIT_MS = 3000;

async function waitStable(page, label) {
  await page.waitForLoadState("load");
  await page
    .evaluate((ms) => {
      const timeout = new Promise((resolve) => setTimeout(resolve, ms));
      const fonts = document.fonts ? document.fonts.ready : Promise.resolve();
      return Promise.race([fonts, timeout]);
    }, STABLE_WAIT_MS)
    .catch(() => {});
  // The DAL "Alight" widget has two custom element tags -- the single-field
  // text-input combobox (<autocomplete-select-input>, e.g. the case filter's
  // "client" field) and the plain/multi <select>-based one
  // (<autocomplete-select>, e.g. advicer/area/issues/community on the
  // advices filter) -- both upgrade asynchronously, adding data-bound="true"
  // some time after load. Confirmed live for both: two otherwise-identical
  // captures raced this and differed only in whether the upgrade had
  // finished yet.
  await page
    .evaluate((ms) => {
      const timeout = new Promise((resolve) => setTimeout(resolve, ms));
      const ready = new Promise((resolve) => {
        const check = () => {
          const ok = Array.from(
            document.querySelectorAll("autocomplete-select-input, autocomplete-select")
          ).every((el) => el.dataset.bound === "true");
          if (ok) resolve();
          else setTimeout(check, 100);
        };
        check();
      });
      return Promise.race([ready, timeout]);
    }, STABLE_WAIT_MS)
    .catch(() => {});
  // TinyMCE sets style="visibility: hidden; height: 500px" on .tox-tinymce
  // while it boots, then clears "visibility: hidden" once ready -- without
  // waiting for that, screenshots raced TinyMCE's own init and came out
  // with a different page height (~25px) between two otherwise-identical
  // captures, even though the (later DOM-sanitized) HTML was byte-identical
  // both times. Confirmed live.
  await page
    .evaluate((ms) => {
      const timeout = new Promise((resolve) => setTimeout(resolve, ms));
      const ready = new Promise((resolve) => {
        const check = () => {
          const ok = Array.from(document.querySelectorAll(".tox-tinymce")).every(
            (el) => el.style.visibility !== "hidden"
          );
          if (ok) resolve();
          else setTimeout(check, 100);
        };
        check();
      });
      return Promise.race([ready, timeout]);
    }, STABLE_WAIT_MS)
    .catch(() => {});
  // Every *_datatables.js-driven table (cases/letters/advicer/users/events -
  // see plan.md M2's file list) gets its initial rows from an async AJAX
  // call that the page `load` event does not wait for. Originally this
  // waited for `tbody tr` to be non-empty, which is wrong: DataTables
  // renders its own single placeholder row while loading
  // (`<tr><td class="dt-empty">Wczytywanie...</td></tr>`), which already
  // satisfies "non-empty tbody" - confirmed live by tracing the exact DOM
  // transition (one row, class dt-empty, text "Wczytywanie..." -> 100ms
  // later, 16 real rows, no dt-empty). That's why raising the wait budget
  // from 8s to 15s never reduced the staff_cases_datatable mobile flake:
  // the check was satisfied in under 100ms every time, on the wrong state,
  // regardless of budget. DataTables' own `#<id>_processing` indicator
  // (visibly "Przetwarzanie...") is the actual, correct signal - it's
  // `display: block` while a request is in flight and `none` once settled,
  // whether the real result set is empty or not.
  const DATATABLE_IDS = [
    "datatable_cases",
    "datatable_letters",
    "datatable_advices",
    "datatable_users",
    "datatable_events",
  ];
  // NOTE: Playwright's page.evaluate(fn, arg) takes exactly one arg (unlike
  // Puppeteer, it does NOT accept extra positional arguments) - bundle
  // multiple values into one object. Passing them as separate arguments
  // throws synchronously ("Too many arguments..."), which the .catch(() =>
  // {}) below was silently swallowing - confirmed live as the actual root
  // cause of this whole wait being a complete no-op despite looking
  // correct, which is why neither raising the timeout nor rewriting the
  // wait condition itself ever changed the staff_cases_datatable flake
  // rate: the code computing that condition was never running at all.
  const processingWaitResult = await page
    .evaluate(({ ids, ms }) => {
      const start = Date.now();
      const stillProcessing = () =>
        ids.some((id) => {
          const indicator = document.getElementById(`${id}_processing`);
          return indicator && getComputedStyle(indicator).display !== "none";
        });
      const present = ids.some((id) => document.getElementById(`${id}_processing`));
      const timeout = new Promise((resolve) => setTimeout(() => resolve("timeout"), ms));
      const ready = new Promise((resolve) => {
        const check = () => {
          if (!stillProcessing()) resolve("ready");
          else setTimeout(check, 100);
        };
        check();
      });
      return Promise.race([ready, timeout]).then((outcome) => ({
        present,
        outcome,
        elapsedMs: Date.now() - start,
      }));
    }, { ids: DATATABLE_IDS, ms: 15000 })
    .catch(() => null);
  // Temporary diagnostic for the staff_cases_datatable flake (see
  // logs/wcag/README.md): logs whether a DataTable was present on this
  // page at all, and whether the _processing wait resolved on signal or
  // hit the full 15s budget, so a CI run tells us whether the timeout
  // itself is too short or something else entirely is going on. Remove
  // once the flake is understood.
  if (label && processingWaitResult && processingWaitResult.present) {
    console.log(
      `[datatable-wait] ${label}: outcome=${processingWaitResult.outcome} ` +
        `elapsedMs=${processingWaitResult.elapsedMs}`
    );
  }
  // Rows existing in the DOM isn't the same as DataTables having finished
  // its own post-insert layout pass (column width/scroll-wrapper sizing) -
  // harmless to keep as a secondary settle check now that the wait above
  // is gated on the correct signal.
  await page
    .evaluate(({ ids, ms }) => {
      const timeout = new Promise((resolve) => setTimeout(resolve, ms));
      const ready = new Promise((resolve) => {
        let lastSizes = null;
        const sizesOf = () =>
          ids
            .map((id) => document.getElementById(id))
            .filter(Boolean)
            .map((t) => `${t.scrollWidth}x${t.offsetHeight}`)
            .join(",");
        const check = () => {
          const sizes = sizesOf();
          if (sizes === lastSizes) {
            resolve();
            return;
          }
          lastSizes = sizes;
          setTimeout(check, 150);
        };
        check();
      });
      return Promise.race([ready, timeout]);
    }, { ids: DATATABLE_IDS, ms: 3000 })
    .catch(() => {});
  await page.addStyleTag({ content: DISABLE_ANIMATIONS_CSS });
}

// TinyMCE (letters/events forms) renders its own toolbar chrome with
// computed inline pixel widths and internal ids that vary run-to-run even
// with nothing else changing on the page (confirmed live: two consecutive
// captures of the same form differed only inside .tox-tinymce). It's
// third-party widget chrome, not page content the audit cares about, so it
// gets collapsed to a fixed placeholder before every HTML capture.
async function sanitizeDom(page) {
  await page
    .evaluate(() => {
      document.querySelectorAll(".tox-tinymce").forEach((el) => {
        el.innerHTML = "<!-- TINYMCE_WIDGET_NORMALIZED -->";
        el.removeAttribute("style");
      });
    })
    .catch(() => {});
}

async function pageHtml(page) {
  await sanitizeDom(page);
  return page.content();
}

function writeHtml(dir, stateId, html) {
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, `${stateId}.html`), normalizeHtml(html), "utf8");
}

async function writeScreenshot(page, dir, stateId, viewportName) {
  fs.mkdirSync(dir, { recursive: true });
  await page.screenshot({
    path: path.join(dir, `${stateId}-${viewportName}.png`),
    fullPage: true,
    animations: "disabled",
  });
}

async function runInteraction(page, kind) {
  switch (kind) {
    // The DataTables fork is explicitly jQuery-free (django-ajax-datatables.net.v3,
    // "fork rewritten for DataTables.net v3, jQuery-free frontend" -- there is no
    // window.jQuery at all). DataTables v3's own vanilla `new DataTable(selector)`
    // returns the existing instance's API if the table is already initialized,
    // rather than re-initializing it.
    case "datatable_page_length_25":
      await page.waitForSelector("#datatable_cases", { state: "attached" });
      await page.evaluate(() => new window.DataTable("#datatable_cases").page.len(25).draw());
      break;
    case "datatable_sort_name":
      await page.waitForSelector("#datatable_cases", { state: "attached" });
      await page.evaluate(() =>
        new window.DataTable("#datatable_cases").order([[2, "asc"]]).draw()
      );
      break;
    case "datatable_filter":
      await page.waitForSelector("#datatable_cases", { state: "attached" });
      await page.evaluate(() =>
        new window.DataTable("#datatable_cases").search("Odwołanie").draw()
      );
      break;
    case "attachment_text_modal": {
      // attachment id=1 (sample.png), letter 2, in the 5-message thread --
      // safely on page 1 regardless of any pagination of the record list.
      const btn = page.locator(
        'button[hx-get*="/listy/attachments/1/text-content-modal/"]'
      );
      await btn.waitFor({ state: "visible", timeout: 5000 });
      await btn.click();
      break;
    }
    case "ai_reject_modal_open": {
      // Opens the Bootstrap modal only -- does NOT click "Reject" inside it,
      // which would hx-post and permanently mark the seeded
      // N8nArticlesSearchRequest as rejected, breaking repeatability.
      const btn = page.locator('button[data-bs-target="#aiSearchRejectModal-10"]');
      await btn.waitFor({ state: "visible", timeout: 5000 });
      await btn.click();
      await page.waitForSelector("#aiSearchRejectModal-10.show", { timeout: 5000 });
      // The dialog's own .show class can land slightly before the backdrop
      // finishes painting (confirmed live -- an intermittent ~45% mobile
      // screenshot diff on this exact interaction, backdrop-not-yet-drawn
      // vs backdrop-drawn). Waiting for the backdrop too closes that gap.
      await page.waitForSelector(".modal-backdrop.show", { timeout: 5000 }).catch(() => {});
      break;
    }
    case "dal_dropdown_open": {
      // The DAL "Alight" widget's underlying <input>, inside its custom
      // element (see waitStable's data-bound wait above).
      const input = page.locator('input[name="client-input"]').first();
      await input.waitFor({ state: "visible", timeout: 5000 });
      await input.click();
      await input.type("a", { delay: 50 });
      await page.waitForTimeout(400); // debounced remote fetch
      break;
    }
    case "navsearch_modal_open": {
      const trigger = page.locator('a[data-bs-target="#navsearch_modal"]').first();
      await trigger.waitFor({ state: "visible", timeout: 5000 });
      await trigger.click();
      await page.waitForSelector("#navsearch_modal.show", { timeout: 5000 });
      break;
    }
    default:
      throw new Error(`Unknown interaction kind: ${kind}`);
  }
  await page.waitForTimeout(500);
}

// Captures one viewport's worth of screenshots (postload + every
// interaction) via its OWN fresh page load. Deliberately NOT a single page
// resized between shots: this page's DataTables init (case_datatables.js)
// computes scrollY from the viewport height present at DOMContentLoaded and
// never recalculates it, so resizing an already-loaded desktop page down to
// mobile left the table's internal layout stuck at the wrong size -- a
// ~1.9% whole-page pixel diff that moved between different states across
// runs, confirmed live. Loading fresh at the target viewport is also just
// more faithful to how a real mobile visitor would arrive at the page.
async function captureViewportPass(context, entry, viewportName, viewport, shotDir, writeHtmlTo, report) {
  const page = await context.newPage();
  page.setDefaultTimeout(10000); // well under Playwright's 30s default
  await page.setViewportSize(viewport);
  await page.goto(entry.path, { waitUntil: "load" });
  await waitStable(page, `${entry.id}/${viewportName}/postload`);
  if (writeHtmlTo) writeHtml(writeHtmlTo, "postload", await pageHtml(page));
  await writeScreenshot(page, shotDir, "postload", viewportName);

  for (const kind of entry.interactions || []) {
    try {
      await runInteraction(page, kind);
      if (writeHtmlTo) writeHtml(writeHtmlTo, kind, await pageHtml(page));
      await writeScreenshot(page, shotDir, kind, viewportName);
      if (viewportName === "desktop") {
        report.push({ id: entry.id, role: entry.role, interaction: kind, ok: true });
      }
    } catch (err) {
      if (viewportName === "desktop") {
        report.push({
          id: entry.id, role: entry.role, interaction: kind, ok: false, error: err.message,
        });
      }
    }
  }
  await page.close();
}

async function captureEntry(browser, roleStates, entry, htmlRoot, shotRoot, report) {
  const context = await browser.newContext({
    baseURL: BASE_URL,
    storageState: roleStates[entry.role] || undefined,
  });
  const htmlDir = path.join(htmlRoot, entry.role, entry.id);
  const shotDir = path.join(shotRoot, entry.role, entry.id);

  try {
    const apiResp = await context.request.get(entry.path);
    const status = apiResp.status();
    const allowed = entry.allowStatus || [200];
    writeHtml(htmlDir, "server", await apiResp.text());

    const row = { id: entry.id, role: entry.role, path: entry.path, status, expected: allowed };
    row.statusOk = allowed.includes(status);
    report.push(row);

    if (entry.isJson) {
      return;
    }

    // HTML content isn't viewport-dependent (CSS-only responsive layout,
    // no server-side UA sniffing) -- only captured on the desktop pass.
    await captureViewportPass(context, entry, "desktop", VIEWPORTS.desktop, shotDir, htmlDir, report);
    await captureViewportPass(context, entry, "mobile", VIEWPORTS.mobile, shotDir, null, report);
  } finally {
    await context.close();
  }
}

// Runs the full SAMPLE capture, writing html to htmlRoot and screenshots to
// shotRoot. Returns the report array (status codes + interaction results).
async function capture(htmlRoot, shotRoot) {
  const browser = await chromium.launch();
  const roleStates = {};
  for (const entry of SAMPLE) {
    if (!(entry.role in roleStates)) {
      roleStates[entry.role] = await loginStorageState(entry.role);
    }
  }

  const report = [];
  for (const entry of SAMPLE) {
    const startedAt = Date.now();
    await captureEntry(browser, roleStates, entry, htmlRoot, shotRoot, report);
    process.stdout.write(
      `captured ${entry.role}/${entry.id} (${Date.now() - startedAt}ms)\n`
    );
  }
  await browser.close();
  return report;
}

// Extracts a mode-agnostic "what can a user actually do and read"
// fingerprint from the current page: form field names (per form),
// actionable-control targets (links/buttons), and the main content area's
// text. Used by equivalence_test.js to compare normal vs WCAG mode without
// requiring byte-identical markup - see
// logs/wcag/plan/ui-mode-design.md §9 and plan.md M0's CI note. WCAG mode
// is allowed to ADD accessible text (visually-hidden labels, live regions);
// it must not drop or rename any form field or actionable target.
async function extractSemantics(page) {
  const semantics = await page.evaluate(() => {
    const norm = (s) => (s || "").replace(/\s+/g, " ").trim();
    const forms = Array.from(document.forms)
      .map((f) => ({
        action: f.getAttribute("action") || "",
        method: (f.getAttribute("method") || "get").toLowerCase(),
        fields: Array.from(f.elements)
          .map((el) => el.name)
          .filter(Boolean)
          .sort(),
      }))
      .sort((a, b) => (a.action + a.method).localeCompare(b.action + b.method));
    const controls = Array.from(document.querySelectorAll("a[href], button"))
      .map((el) => {
        if (el.tagName === "A") return `a:${el.getAttribute("href") || ""}`;
        const form = el.closest("form");
        return `button:${form ? form.getAttribute("action") || "" : ""}:${
          el.getAttribute("type") || "submit"
        }`;
      })
      .sort();
    // M1/F001 added <main id="main-content">, but scoped tightly around
    // just {% block content %} per the audit's own fix (findings.csv F001)
    // - breadcrumbs and Django messages sit in .content but outside
    // <main>, in both modes. .content stays the right text-comparison
    // scope here since this check cares about "same visible information
    // between modes", not the landmark structure itself (that's axe's job).
    const main = document.querySelector(".content") || document.body;
    return { forms, controls, mainText: norm(main.innerText) };
  });
  // Relative-time text ("5 minut temu") legitimately changes between the
  // normal-mode and wcag-mode passes of the same entry, which run minutes
  // apart (see captureSemanticsBothModes) - reuse the same normalization
  // baseline_diff.js relies on so that drift isn't mistaken for WCAG mode
  // dropping content.
  semantics.mainText = normalizeHtml(semantics.mainText);
  return semantics;
}

async function captureEntrySemantics(browser, roleStates, entry) {
  if (entry.isJson) return {};
  const context = await browser.newContext({
    baseURL: BASE_URL,
    storageState: roleStates[entry.role] || undefined,
  });
  try {
    const page = await context.newPage();
    page.setDefaultTimeout(10000);
    await page.setViewportSize(VIEWPORTS.desktop);
    await page.goto(entry.path, { waitUntil: "load" });
    await waitStable(page, `${entry.id}/semantics`);

    const states = { postload: await extractSemantics(page) };
    for (const kind of entry.interactions || []) {
      try {
        await runInteraction(page, kind);
        states[kind] = await extractSemantics(page);
      } catch (err) {
        states[kind] = { error: err.message };
      }
    }
    await page.close();
    return states;
  } finally {
    await context.close();
  }
}

// Runs the full SAMPLE through both normal and wcag UI modes, returning
// { "<role>/<id>": { "<state>": { normal, wcag } } } for
// equivalence_test.js to diff. No disk I/O - this is a semantic comparison,
// not a byte/pixel one, so it doesn't share output dirs with capture().
async function captureSemanticsBothModes() {
  const browser = await chromium.launch();
  const result = {};
  try {
    for (const mode of ["normal", "wcag"]) {
      const roleStates = {};
      for (const entry of SAMPLE) {
        if (!(entry.role in roleStates)) {
          roleStates[entry.role] = await loginStorageState(entry.role, mode);
        }
      }
      for (const entry of SAMPLE) {
        if (entry.isJson) continue;
        const key = `${entry.role}/${entry.id}`;
        result[key] = result[key] || {};
        const states = await captureEntrySemantics(browser, roleStates, entry);
        for (const [stateName, semantics] of Object.entries(states)) {
          result[key][stateName] = result[key][stateName] || {};
          result[key][stateName][mode] = semantics;
        }
        process.stdout.write(`semantics(${mode}): ${key}\n`);
      }
    }
  } finally {
    await browser.close();
  }
  return result;
}

module.exports = {
  capture,
  VIEWPORTS,
  waitStable,
  runInteraction,
  captureSemanticsBothModes,
};
