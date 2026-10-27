// Normal-mode golden-master capture. See logs/wcag/HANDOFF.md section 5 and
// logs/wcag/plan/plan.md M0's CI note (promoted from logs/wcag/scripts/).
//
// HTML is the committed baseline (tracked in git - small, text, reviewable
// diffs) that baseline_diff.js's CI gate actually diffs against. Screenshots
// are local-only evidence (gitignored under logs/wcag/, same as before) for
// a human to visually sanity-check a change - see
// logs/wcag/README.md §5 for why: PNGs don't delta well in git, and
// HTML-diff + the existing compiled-asset-hash check already cover the
// regression categories that matter for a server-rendered Django app.
//
// Writes:
//   tests/wcag/playwright/baseline/html/<role>/<id>/{server,postload,<interaction>}.html  (COMMIT this)
//   logs/wcag/baseline/screenshots/<role>/<id>/{postload,<interaction>}-{desktop,mobile}.png  (local only)
//   logs/wcag/baseline/capture-report.json  (status codes, interaction errors - local only)
//
// Run: node tests/wcag/playwright/baseline_capture.js
// Requires A11Y_SEED_PASSWORD; the app must be up against poradnia_a11y
// (see logs/wcag/README.md).
const fs = require("fs");
const path = require("path");

const { capture } = require("./lib/capture_core");
const { SAMPLE } = require("./sample");

const OUT_HTML = path.join(__dirname, "baseline", "html");
const LOCAL_ROOT = path.join(__dirname, "..", "..", "..", "logs", "wcag");
const OUT_SHOT = path.join(LOCAL_ROOT, "baseline", "screenshots");

async function main() {
  const report = await capture(OUT_HTML, OUT_SHOT);

  fs.mkdirSync(path.join(LOCAL_ROOT, "baseline"), { recursive: true });
  fs.writeFileSync(
    path.join(LOCAL_ROOT, "baseline", "capture-report.json"),
    JSON.stringify(report, null, 2),
    "utf8"
  );

  const badStatus = report.filter((r) => r.path && !r.statusOk);
  const badInteraction = report.filter((r) => r.interaction && !r.ok);
  console.log(`\nCaptured ${SAMPLE.length} sample entries.`);
  if (badStatus.length) {
    console.log(`WARNING: ${badStatus.length} entries returned an unexpected status:`);
    badStatus.forEach((r) => console.log(`  ${r.role}/${r.id} ${r.path} -> ${r.status}`));
  }
  if (badInteraction.length) {
    console.log(`WARNING: ${badInteraction.length} interactions failed:`);
    badInteraction.forEach((r) => console.log(`  ${r.role}/${r.id} ${r.interaction}: ${r.error}`));
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
