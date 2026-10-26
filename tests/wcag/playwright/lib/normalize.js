// Normalisation rules applied to captured HTML before it's written to
// baseline/html or compared by baseline_diff.js. See logs/wcag/README.md
// "Normalisation rules" for the human-readable list; keep that in sync with
// this file's RULES array (label comes straight from here).

const POLISH_MONTHS =
  "stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia";

const RULES = [
  {
    label: "CSRF token (csrfmiddlewaretoken hidden input value)",
    re: /name="csrfmiddlewaretoken" value="[^"]*"/g,
    replacement: 'name="csrfmiddlewaretoken" value="[CSRF]"',
  },
  {
    label: "App version tag (templates/base.html `v{% poradnia_version %}`)",
    re: /v\d+\.\d+\.\d+(-dev)?/g,
    replacement: "[VERSION]",
  },
  {
    label: "ISO-ish date/datetime (YYYY-MM-DD[ T]HH:MM[:SS])",
    re: /\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?/g,
    replacement: "[DATETIME]",
  },
  {
    label: "Polish absolute date (\"14 października 2026\")",
    re: new RegExp(`\\d{1,2}\\s+(${POLISH_MONTHS})\\s+\\d{4}`, "g"),
    replacement: "[DATE]",
  },
  {
    // crispy-forms' DateTimePicker inputs (e.g. advicer's "grant_on" field)
    // default their value to today when unset, rendered DD.MM.YYYY - not
    // covered by the ISO-ish rule above. Confirmed live: a baseline
    // captured one day and re-diffed the next showed exactly this field
    // changing (26.10.2026 -> 27.10.2026), nothing else - a real gap, not a
    // flake, that would have recurred every midnight regardless.
    label: "Polish dotted date (DD.MM.YYYY, e.g. advice-form's default grant_on value)",
    re: /\b\d{2}\.\d{2}\.\d{4}\b/g,
    replacement: "[DATE]",
  },
  {
    label: "Bare time (HH:MM[:SS])",
    re: /\b\d{2}:\d{2}(:\d{2})?\b/g,
    replacement: "[TIME]",
  },
  {
    // humanize/naturaltime renders these with &nbsp; (not a literal space)
    // between the number and the unit, e.g. "8&nbsp;minut temu". The count
    // is optional - Polish singular phrasing drops it entirely ("minutę
    // temu", "godzinę temu", confirmed live: these recur every time a
    // seeded event's timestamp happens to land within the last minute/hour
    // of "now", which it eventually always will since the seed data's
    // ages are fixed but wall-clock "now" keeps moving). Matching the
    // generic "<word ending in 'temu'>" shape rather than enumerating every
    // Polish grammatical case (minuta/minutę/minuty/minut, ...) avoids
    // re-finding the same gap for every unit one at a time. Must be
    // \p{L}+ (letters only), not a "non-whitespace" class: an earlier
    // version used [^\s<>&]+ and that also matches "=" and '"', so on the
    // no-digit singular form it greedily walked backward into
    // title="minutę and ate the attribute syntax itself (confirmed live --
    // produced `<span [RELATIVE_TIME]">`, missing `title="`). Letters-only
    // stops dead at "=", which isn't a letter.
    label: "Polish relative time (\"3 dni temu\", \"minutę temu\", ...)",
    re: /\b(?:\d+(?:\s|&nbsp;)+)?[\p{L}]+(?:\s|&nbsp;)+temu\b/giu,
    replacement: "[RELATIVE_TIME]",
  },
  {
    // {% github_link %} (templates/base.html footer) renders the checked-
    // out commit's short hash twice - in the compare URL and as the link
    // text - so it drifts on every commit regardless of any actual
    // normal-mode output change. Listed in HANDOFF's own normalisation
    // list ("poradnia_version and the GitHub revision") but never
    // actually wired in here until found live: baseline_diff.js flagged
    // this footer line as a false-positive change after two ordinary
    // commits landed with no template changes at all.
    label: "GitHub revision link ({% github_link %}, templates/base.html footer)",
    re: /(href="https:\/\/github\.com\/watchdogpolska\/poradnia\/compare\/)[0-9a-f]{6,40}(\.\.\.[^"]*")>[0-9a-f]{6,40}(<\/a>)/g,
    replacement: "$1[GITHUB_REVISION]$2>[GITHUB_REVISION]$3",
  },
];

// Attribute order has no semantic meaning in HTML, but it isn't always
// deterministic: DataTables' own ScrollX/ARIA pass (which adds
// `role="columnheader"` to header cells missing one) races against this
// app's own per-table `initComplete` handlers (e.g. events_datatables.js's
// filter-row padding fix) that set other attributes on the same header
// cells - whichever runs first wins that slot in the serialized attribute
// order. Confirmed live: baseline_diff flagged
// `<th style="padding: 0px;" role="columnheader">` vs
// `<th role="columnheader" style="padding: 0px;">` on a DataTable filter
// row between two captures of identical seed data - same two attributes,
// same values, just swapped. Sorting every tag's attributes alphabetically
// makes comparison insensitive to that race without hiding an actual
// content change. Deliberately a regex pass (consistent with the RULES
// above), not a full HTML parser - this is test-comparison tooling, not a
// renderer, and a false "no tags matched" is far cheaper here than a new
// parser dependency.
const TAG_RE =
  /<([a-zA-Z][a-zA-Z0-9:-]*)((?:\s+[^\s"'>/=]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*)\s*(\/?)>/g;
const ATTR_RE = /[^\s"'>/=]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?/g;

function sortTagAttributes(html) {
  return html.replace(TAG_RE, (match, tagName, attrsStr, selfClose) => {
    if (!attrsStr || !attrsStr.trim()) return match;
    const attrs = Array.from(attrsStr.matchAll(ATTR_RE)).map((m) => m[0]);
    attrs.sort((a, b) => a.localeCompare(b));
    return `<${tagName} ${attrs.join(" ")}${selfClose ? " /" : ""}>`;
  });
}

function normalizeHtml(html) {
  const withRulesApplied = RULES.reduce((acc, rule) => acc.replace(rule.re, rule.replacement), html);
  return sortTagAttributes(withRulesApplied);
}

module.exports = { normalizeHtml, RULES, sortTagAttributes };
