// HTML validation of the rendered DOM (HANDOFF.md §6.4.1 — 4.1.1 Parsing,
// duplicate ids). Reuses the HTML already captured by baseline_capture.js
// (baseline/html/<role>/<id>/*.html) instead of re-navigating -- it's
// already the post-load, post-interaction serialized DOM for every state
// sample.js defines, so there's nothing to re-render.
//
// Run: node tests/wcag/playwright/validate_html.js
// (no live app / credentials needed -- pure static-file validation)
const fs = require("fs");
const path = require("path");
const { HtmlValidate } = require("html-validate");

const BASELINE_HTML = path.join(__dirname, "baseline", "html");
const ROOT = path.join(__dirname, "..", "..", "..", "logs", "wcag");
const OUT_DIR = path.join(ROOT, "audit", "evidence", "html-validate");

// Deliberately NOT html-validate:recommended -- that preset's rules are
// mostly code-style (no-trailing-whitespace, require-sri, no-inline-style,
// no-conditional-comment, script-type, ...), not accessibility, and drowned
// out the real findings (7375 whitespace "violations" on a captured-DOM
// file is noise, not signal). a11y + document covers what HANDOFF §6.4.1
// actually asks for: 4.1.1 parsing (duplicate ids, parse errors are always
// reported regardless of rule config) plus the wcag/h* a11y rule family.
const hv = new HtmlValidate({
  extends: ["html-validate:a11y", "html-validate:document"],
  rules: {
    "no-dup-id": "error",
    // Confirmed deliberate project behaviour (CLAUDE.md): <html lang="pl">
    // is set correctly; this rule is about void-element self-closing style,
    // which this codebase (and most hand-authored Django HTML) doesn't
    // follow -- not a finding.
    "void-style": "off",
    // Subresource Integrity is a CDN-script security hardening practice,
    // not a WCAG concern -- out of scope here (pulled in by the "document"
    // preset, not "a11y").
    "require-sri": "off",
  },
});

function listFilesRecursive(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...listFilesRecursive(full));
    else if (entry.name.endsWith(".html")) out.push(full);
  }
  return out;
}

async function main() {
  const files = listFilesRecursive(BASELINE_HTML).filter((f) => f.endsWith("server.html") === false);
  // server.html is the raw pre-JS response -- validating it too would just
  // double-count every issue also present in postload.html (JS doesn't
  // remove markup problems, only add to the DOM). postload/interaction
  // states are the ones that matter for "rendered DOM".

  fs.mkdirSync(OUT_DIR, { recursive: true });
  const report = [];
  const ruleCounts = {};

  for (const file of files) {
    const rel = path.relative(BASELINE_HTML, file);
    const html = fs.readFileSync(file, "utf8");
    const result = await hv.validateString(html, file);
    const messages = result.results.flatMap((r) => r.messages);
    if (messages.length === 0) continue;

    const outKey = rel.replace(/[\\/]/g, "__").replace(/\.html$/, "");
    fs.writeFileSync(
      path.join(OUT_DIR, `${outKey}.json`),
      JSON.stringify(messages, null, 2)
    );

    report.push({ file: rel, errorCount: result.errorCount, warningCount: result.warningCount });
    for (const m of messages) {
      ruleCounts[m.ruleId] = (ruleCounts[m.ruleId] || 0) + 1;
    }
  }

  fs.writeFileSync(
    path.join(ROOT, "audit", "evidence", "html-validate-report.json"),
    JSON.stringify(report, null, 2)
  );

  console.log(`validate_html: ${files.length} files checked, ${report.length} with issues.`);
  for (const [rule, count] of Object.entries(ruleCounts).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${rule}: ${count}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
