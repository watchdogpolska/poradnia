// Re-captures the sample into a throwaway tmp dir and diffs it against the
// stored baseline. See logs/wcag/HANDOFF.md section 5. This is the
// normal-mode CI gate: see logs/wcag/plan/plan.md M0's CI note.
//
// Two different baselines, two different purposes (see
// logs/wcag/README.md §5 for the full reasoning):
//   - tests/wcag/playwright/baseline/{html,assets.sha256} is COMMITTED and is
//     what this script actually diffs against in CI (and locally).
//   - logs/wcag/baseline/screenshots/ is local-only (gitignored), regenerated
//     by baseline_capture.js for a human to eyeball - not diffed here at
//     all unless it happens to exist locally, in which case it's checked
//     too as a bonus (see diffScreenshots below: gracefully skipped with a
//     NOTE, not a failure, if the directory is absent - which it always is
//     in CI).
//
// Fails (exit 1) on: any normalized-HTML diff, a bundle hash change
// (tests/wcag/playwright/baseline/assets.sha256), or - only when the local
// screenshot baseline happens to be present - a pixel diff above a tiny
// anti-aliasing threshold.
//
// Run: node tests/wcag/playwright/baseline_diff.js
const fs = require("fs");
const path = require("path");
const os = require("os");
const { PNG } = require("pngjs");
const pixelmatch = require("pixelmatch").default || require("pixelmatch");

const { capture } = require("./lib/capture_core");

const BASELINE_HTML = path.join(__dirname, "baseline", "html");
const ASSETS_SHA_PATH = path.join(__dirname, "baseline", "assets.sha256");
const LOCAL_ROOT = path.join(__dirname, "..", "..", "..", "logs", "wcag");
const BASELINE_SHOT = path.join(LOCAL_ROOT, "baseline", "screenshots");

// Fraction of pixels allowed to differ (anti-aliasing only) before a
// screenshot counts as a real diff. 0.1% was too tight in practice: static
// text-only pages (terms/privacy) showed ~0.13-0.15% sub-pixel font-hinting
// jitter between two otherwise-identical captures with nothing dynamic on
// the page at all -- confirmed live, bumped to 0.2%.
const PIXEL_DIFF_THRESHOLD = 0.002;

function listFilesRecursive(dir) {
  if (!fs.existsSync(dir)) return [];
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...listFilesRecursive(full));
    } else {
      out.push(full);
    }
  }
  return out;
}

// Temporary diagnostic for the staff_cases_datatable flake (see
// logs/wcag/README.md): "HTML CHANGED" alone doesn't say what changed, and
// this script discards its tmp capture before exiting, so a failing CI run
// gave no way to see the actual content difference. No diff library is
// available here (tests/wcag/playwright has none as a dependency), so this
// is a plain line-by-line comparison, not a real diff algorithm - good
// enough to show a handful of differing lines with context. Remove once
// the flake is understood.
function logLineDiff(label, a, b) {
  const linesA = a.split("\n");
  const linesB = b.split("\n");
  console.log(`[line-diff] ${label}: ${linesA.length} vs ${linesB.length} lines`);
  const max = Math.max(linesA.length, linesB.length);
  let shown = 0;
  for (let i = 0; i < max && shown < 5; i++) {
    if (linesA[i] !== linesB[i]) {
      console.log(`[line-diff] ${label} line ${i + 1}:`);
      console.log(`[line-diff]   - ${JSON.stringify(linesA[i] ?? "<missing>").slice(0, 500)}`);
      console.log(`[line-diff]   + ${JSON.stringify(linesB[i] ?? "<missing>").slice(0, 500)}`);
      shown++;
    }
  }
}

function diffHtml(baselineDir, tmpDir, relPrefix, diffs) {
  const baselineFiles = listFilesRecursive(baselineDir).filter((f) => f.endsWith(".html"));
  for (const baselineFile of baselineFiles) {
    const rel = path.relative(baselineDir, baselineFile);
    const tmpFile = path.join(tmpDir, rel);
    if (!fs.existsSync(tmpFile)) {
      diffs.push(`MISSING in re-capture: ${relPrefix}/${rel}`);
      continue;
    }
    const a = fs.readFileSync(baselineFile, "utf8");
    const b = fs.readFileSync(tmpFile, "utf8");
    if (a !== b) {
      diffs.push(`HTML CHANGED: ${relPrefix}/${rel}`);
      logLineDiff(`${relPrefix}/${rel}`, a, b);
    }
  }
  const tmpFiles = listFilesRecursive(tmpDir).filter((f) => f.endsWith(".html"));
  for (const tmpFile of tmpFiles) {
    const rel = path.relative(tmpDir, tmpFile);
    if (!fs.existsSync(path.join(baselineDir, rel))) {
      diffs.push(`NEW in re-capture (not in baseline): ${relPrefix}/${rel}`);
    }
  }
}

function diffScreenshots(baselineDir, tmpDir, relPrefix, diffs) {
  if (!fs.existsSync(baselineDir)) {
    diffs.push(
      "NOTE: local screenshot baseline not present (local-only by design, not committed -- " +
        "run baseline_capture.js first if you want this check) -- pixel diff skipped"
    );
    return;
  }
  const baselineFiles = listFilesRecursive(baselineDir).filter((f) => f.endsWith(".png"));
  for (const baselineFile of baselineFiles) {
    const rel = path.relative(baselineDir, baselineFile);
    const tmpFile = path.join(tmpDir, rel);
    if (!fs.existsSync(tmpFile)) {
      diffs.push(`MISSING screenshot in re-capture: ${relPrefix}/${rel}`);
      continue;
    }
    const imgA = PNG.sync.read(fs.readFileSync(baselineFile));
    const imgB = PNG.sync.read(fs.readFileSync(tmpFile));
    if (imgA.width !== imgB.width || imgA.height !== imgB.height) {
      diffs.push(
        `SCREENSHOT SIZE CHANGED: ${relPrefix}/${rel} (${imgA.width}x${imgA.height} -> ${imgB.width}x${imgB.height})`
      );
      continue;
    }
    const diffPixels = pixelmatch(imgA.data, imgB.data, null, imgA.width, imgA.height, {
      threshold: 0.1,
    });
    const fraction = diffPixels / (imgA.width * imgA.height);
    if (fraction > PIXEL_DIFF_THRESHOLD) {
      diffs.push(
        `SCREENSHOT PIXEL DIFF: ${relPrefix}/${rel} (${diffPixels} px, ${(fraction * 100).toFixed(3)}%)`
      );
    }
  }
}

function diffAssetHashes(diffs) {
  if (!fs.existsSync(ASSETS_SHA_PATH)) {
    diffs.push("NOTE: baseline/assets.sha256 not present -- bundle-hash check skipped");
    return;
  }
  const crypto = require("crypto");
  const recorded = fs.readFileSync(ASSETS_SHA_PATH, "utf8").trim().split("\n");
  for (const line of recorded) {
    const [hash, file] = line.trim().split(/\s+/);
    if (!file) continue;
    // __dirname is tests/wcag/playwright; the repo root is three levels up.
    const repoRoot = path.join(__dirname, "..", "..", "..");
    const fullPath = path.join(repoRoot, file.replace(/^\*/, ""));
    if (!fs.existsSync(fullPath)) {
      diffs.push(`ASSET MISSING: ${file}`);
      continue;
    }
    const current = crypto.createHash("sha256").update(fs.readFileSync(fullPath)).digest("hex");
    if (current !== hash) {
      diffs.push(`ASSET HASH CHANGED: ${file}`);
    }
  }
}

async function main() {
  const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "poradnia-baseline-diff-"));
  const tmpHtml = path.join(tmpRoot, "html");
  const tmpShot = path.join(tmpRoot, "screenshots");

  try {
    await capture(tmpHtml, tmpShot);

    const diffs = [];
    diffHtml(BASELINE_HTML, tmpHtml, "html", diffs);
    diffScreenshots(BASELINE_SHOT, tmpShot, "screenshots", diffs);
    diffAssetHashes(diffs);

    const failures = diffs.filter((d) => !d.startsWith("NOTE:"));
    const notes = diffs.filter((d) => d.startsWith("NOTE:"));
    notes.forEach((n) => console.log(n));

    if (failures.length === 0) {
      console.log("baseline_diff: OK -- zero diffs.");
      process.exit(0);
    } else {
      console.log(`baseline_diff: ${failures.length} diff(s) found:\n`);
      failures.forEach((d) => console.log(`  - ${d}`));
      process.exit(1);
    }
  } finally {
    fs.rmSync(tmpRoot, { recursive: true, force: true });
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
