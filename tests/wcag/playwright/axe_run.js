// Runs axe-core against every sample.js entry x state x viewport. See
// HANDOFF.md §6.4.1: tags wcag2a/wcag2aa/wcag21a/wcag21aa/wcag22aa,
// re-run after every HTMX swap / modal open / DataTables draw / DAL
// dropdown open (i.e. every "state" sample.js already defines). This is the
// WCAG-mode CI gate: see logs/wcag/plan/plan.md M0's CI note.
//
// Writes one JSON file per (entry, state, viewport) to
// logs/wcag/audit/evidence/axe/<role>__<id>__<state>__<viewport>.json, plus
// an aggregate logs/wcag/audit/evidence/axe-summary.json (violation id ->
// affected pages).
//
// Run: node tests/wcag/playwright/axe_run.js [--mode=normal|wcag]
// Requires A11Y_SEED_PASSWORD; app must be up against poradnia_a11y.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const { BASE_URL, loginStorageState } = require("./lib/auth");
const { VIEWPORTS, waitStable, runInteraction } = require("./lib/capture_core");
const { SAMPLE } = require("./sample");

const MODE = (process.argv.find((a) => a.startsWith("--mode=")) || "--mode=wcag").split(
  "="
)[1];

const ROOT = path.join(__dirname, "..", "..", "..", "logs", "wcag");
const OUT_DIR = path.join(ROOT, "audit", "evidence", "axe");
const AXE_SCRIPT = path.join(__dirname, "node_modules", "axe-core", "axe.min.js");

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

async function runAxe(page) {
  await page.addScriptTag({ path: AXE_SCRIPT });
  return page.evaluate((tags) => {
    return window.axe.run(document, { runOnly: { type: "tag", values: tags } });
  }, TAGS);
}

function summarize(results) {
  return {
    url: results.url,
    violations: results.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      tags: v.tags,
      description: v.description,
      help: v.help,
      helpUrl: v.helpUrl,
      nodeCount: v.nodes.length,
      nodes: v.nodes.map((n) => ({
        target: n.target,
        failureSummary: n.failureSummary,
        html: n.html,
      })),
    })),
    passes: results.passes.length,
    incomplete: results.incomplete.map((v) => ({
      id: v.id,
      impact: v.impact,
      description: v.description,
      nodeCount: v.nodes.length,
    })),
  };
}

async function runOnePass(context, entry, viewportName, viewport, report, summaryAgg) {
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  await page.setViewportSize(viewport);
  await page.goto(entry.path, { waitUntil: "load" });
  await waitStable(page);

  const states = [{ id: "postload" }, ...(entry.interactions || []).map((k) => ({ id: k }))];
  for (const state of states) {
    if (state.id !== "postload") {
      try {
        await runInteraction(page, state.id);
      } catch (err) {
        report.push({
          id: entry.id, role: entry.role, viewport: viewportName, state: state.id,
          error: `interaction failed: ${err.message}`,
        });
        continue;
      }
    }
    let results;
    try {
      results = await runAxe(page);
    } catch (err) {
      report.push({
        id: entry.id, role: entry.role, viewport: viewportName, state: state.id,
        error: `axe failed: ${err.message}`,
      });
      continue;
    }
    const summary = summarize(results);
    const fileKey = `${entry.role}__${entry.id}__${state.id}__${viewportName}`;
    fs.mkdirSync(OUT_DIR, { recursive: true });
    fs.writeFileSync(path.join(OUT_DIR, `${fileKey}.json`), JSON.stringify(summary, null, 2));

    report.push({
      id: entry.id, role: entry.role, viewport: viewportName, state: state.id,
      violationCount: summary.violations.length,
      violationIds: summary.violations.map((v) => v.id),
    });

    for (const v of summary.violations) {
      if (!summaryAgg[v.id]) {
        summaryAgg[v.id] = { impact: v.impact, tags: v.tags, help: v.help, helpUrl: v.helpUrl, pages: [] };
      }
      summaryAgg[v.id].pages.push({ key: fileKey, nodeCount: v.nodeCount });
    }
  }
  await page.close();
}

async function main() {
  console.log(`axe_run: mode=${MODE}`);
  const browser = await chromium.launch();
  const roleStates = {};
  for (const entry of SAMPLE) {
    if (!(entry.role in roleStates)) {
      roleStates[entry.role] = await loginStorageState(entry.role, MODE);
    }
  }

  const report = [];
  const summaryAgg = {};
  for (const entry of SAMPLE) {
    if (entry.isJson) continue;
    const startedAt = Date.now();
    const context = await browser.newContext({
      baseURL: BASE_URL,
      storageState: roleStates[entry.role] || undefined,
    });
    try {
      await runOnePass(context, entry, "desktop", VIEWPORTS.desktop, report, summaryAgg);
      await runOnePass(context, entry, "mobile", VIEWPORTS.mobile, report, summaryAgg);
    } finally {
      await context.close();
    }
    process.stdout.write(`axe: ${entry.role}/${entry.id} (${Date.now() - startedAt}ms)\n`);
  }
  await browser.close();

  fs.writeFileSync(
    path.join(ROOT, "audit", "evidence", "axe-report.json"),
    JSON.stringify(report, null, 2)
  );
  fs.writeFileSync(
    path.join(ROOT, "audit", "evidence", "axe-summary.json"),
    JSON.stringify(summaryAgg, null, 2)
  );

  const totalViolations = report.reduce((sum, r) => sum + (r.violationCount || 0), 0);
  console.log(`\naxe_run: ${report.length} (entry, state, viewport) passes, ${totalViolations} total violation instances.`);
  console.log(`Distinct violation rule ids: ${Object.keys(summaryAgg).length}`);
  for (const [id, data] of Object.entries(summaryAgg).sort((a, b) => b[1].pages.length - a[1].pages.length)) {
    console.log(`  ${id} [${data.impact}] -- ${data.pages.length} page-states affected`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
