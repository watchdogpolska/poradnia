// The equivalence gate: "no feature merges without its WCAG-mode version"
// (logs/wcag/plan/statement-inputs.md, condition 2 / HANDOFF.md §1). Diffs
// a normal-mode capture against a WCAG-mode capture of the same
// sample.js entry×role×state and fails if WCAG mode is missing a form
// field, an actionable control (link/button target), or any text present
// in normal mode. WCAG mode is explicitly allowed to ADD accessible text
// (visually-hidden labels, live regions, skip links) - this only fails on
// loss, not addition. See logs/wcag/plan/ui-mode-design.md §9.
//
// Run: node tests/wcag/playwright/equivalence_test.js
// Requires A11Y_SEED_PASSWORD; app must be up against poradnia_a11y.
const fs = require("fs");
const path = require("path");

const { captureSemanticsBothModes } = require("./lib/capture_core");

const ROOT = path.join(__dirname, "..", "..", "..", "logs", "wcag");
const OUT_DIR = path.join(ROOT, "audit", "evidence");

function wordsOf(text) {
  return (text || "").toLowerCase().split(/\s+/).filter(Boolean);
}

// True if every word in `needle` (with multiplicity) also occurs in
// `haystack` - a bag-of-words containment check, not a substring check, so
// WCAG mode can insert extra text anywhere without breaking this.
function containsAllWords(haystack, needle) {
  const counts = new Map();
  for (const w of haystack) counts.set(w, (counts.get(w) || 0) + 1);
  for (const w of needle) {
    const remaining = counts.get(w) || 0;
    if (remaining <= 0) return false;
    counts.set(w, remaining - 1);
  }
  return true;
}

function diffPair(label, normal, wcag, diffs) {
  if (normal.error || wcag.error) {
    diffs.push(
      `${label}: interaction failed (normal=${normal.error || "ok"}, wcag=${wcag.error || "ok"})`
    );
    return;
  }

  // Containment, not exact equality: WCAG mode is explicitly allowed to ADD
  // forms/controls (e.g. F001's skip link, which has no normal-mode
  // equivalent) - this only fails when something present in normal mode is
  // missing from WCAG mode, never on an addition. Forms are compared by a
  // stable per-form key since object identity/order isn't meaningful here.
  const wcagFormKeys = new Set(wcag.forms.map((f) => JSON.stringify(f)));
  const missingForms = normal.forms
    .map((f) => JSON.stringify(f))
    .filter((key) => !wcagFormKeys.has(key));
  if (missingForms.length > 0) {
    diffs.push(
      `${label}: WCAG mode is missing form(s) present in normal mode: ${missingForms.join(", ")}`
    );
  }

  const wcagControlSet = new Set(wcag.controls);
  const missingControls = normal.controls.filter((c) => !wcagControlSet.has(c));
  if (missingControls.length > 0) {
    diffs.push(
      `${label}: WCAG mode is missing control target(s) present in normal mode: ${missingControls.join(", ")}`
    );
  }

  if (!containsAllWords(wordsOf(wcag.mainText), wordsOf(normal.mainText))) {
    diffs.push(`${label}: WCAG mode is missing text present in normal mode`);
  }
}

async function main() {
  const result = await captureSemanticsBothModes();

  const diffs = [];
  for (const [key, states] of Object.entries(result)) {
    for (const [stateName, pair] of Object.entries(states)) {
      const label = `${key} [${stateName}]`;
      if (!pair.normal || !pair.wcag) {
        diffs.push(`${label}: missing capture for one mode`);
        continue;
      }
      diffPair(label, pair.normal, pair.wcag, diffs);
    }
  }

  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(
    path.join(OUT_DIR, "equivalence-report.json"),
    JSON.stringify({ diffs, raw: result }, null, 2)
  );

  if (diffs.length === 0) {
    console.log("equivalence_test: OK -- normal and wcag mode offer the same forms/controls/content.");
    process.exit(0);
  } else {
    console.log(`equivalence_test: ${diffs.length} diff(s) found:\n`);
    diffs.forEach((d) => console.log(`  - ${d}`));
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
