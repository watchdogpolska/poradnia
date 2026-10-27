# WCAG-mode CI infrastructure

Permanent CI tooling for the `wcag_mode_checks` job in
`.github/workflows/web.yml` (see `plan/plan.md`'s M0 CI note and
`ui-mode-design.md` §9 under `logs/wcag/` for the full design history -
that tree is gitignored/local-only; nothing here depends on it existing).

## Policy: no feature merges without its WCAG-mode version

Poradnia offers two display modes (see the accessibility statement at
`/strony/deklaracja-dostepnosci/` for the public-facing explanation). WCAG
mode must keep offering the same information and functionality as normal
mode, and stay that way as the app evolves - not just on the day it first
reached that state. A PR that adds a control, form, or page only in normal
mode is treated the same as a PR that breaks an existing test: it doesn't
merge. `equivalence_test.js` is the automated half of that check (same
form fields, actionable-control targets, and content in both modes); it
cannot judge whether the WCAG-mode rendering is actually *good*
(semantically correct landmarks, sensible focus order, real labels - not
just "technically present"), which stays a human PR-review step.

## Review cadence

- **Annually, by 31 March** (art. 11 of the Polish digital-accessibility
  act): re-run the full `audit/sample.md` pass (`axe_run.js --mode=wcag`,
  `equivalence_test.js`, `baseline_diff.js`, plus a fresh manual keyboard
  review) and republish the accessibility statement with updated dates and
  any new or resolved non-conformities.
- **After every release**: the three CI gates above catch *regressions*
  automatically on every PR. They do not substitute for the human review
  step described above for *new* WCAG-mode work.

## What's here

- `docker-compose.a11y.yml` - compose override pointing `web` at an
  isolated `poradnia_a11y` database (never `poradnia`/`test_poradnia` - no
  real client data) with MFA/Turnstile/debug-toolbar disabled so a
  Playwright-driven login works deterministically.
- `seed_a11y.py` - standalone seeder (not a management command, kept
  outside the apps on purpose) with a fixed `random.seed`: `--reset`
  always produces the same 65 cases, same subjects, same status
  distribution, same 8 named `a11y_*` login users.
- `playwright/` - the Node/Playwright tooling itself. See its own scripts'
  header comments for what each does; the three CI gates are:
  - `equivalence_test.js` - normal mode vs WCAG mode must offer the same
    form fields, actionable-control targets, and content. No stored
    baseline needed (compares two fresh captures from the same run).
  - `axe_run.js --mode=wcag` - axe-core against WCAG mode.
  - `baseline_diff.js` - normal-mode regression gate, diffs a fresh
    capture against `playwright/baseline/`.

## Committed vs local-only baseline

`playwright/baseline/html/` + `playwright/baseline/assets.sha256` are
**committed to git** - small, text, reviewable as a normal diff. This is
what `baseline_diff.js` actually diffs against, both locally and in CI.

Screenshots are **not** committed - `baseline_capture.js` writes them to
`logs/wcag/baseline/screenshots/` (gitignored) purely as a local visual
sanity-check tool for whoever's regenerating the baseline. PNGs don't
delta well in git and would grow the repo roughly monotonically over time
as normal-mode output changes; HTML-diff plus the compiled-asset hash
check already cover the regression categories that matter for a
server-rendered Django app. `baseline_diff.js` still pixel-diffs against
the local screenshots if they happen to exist, but gracefully no-ops
(logs a `NOTE:`, not a failure) when they don't - which is always the case
in CI.

## Regenerating the baseline

Before committing a PR that changes normal-mode output:

```bash
make wcag-baseline
```

Seeds a throwaway `poradnia_a11y`, brings the app up against it, rebuilds
frontend assets, runs the Playwright capture, then restores the `web`
container to its normal config. Review and commit the result:

```bash
git status playwright/baseline/
git diff playwright/baseline/html/
```

A PR that doesn't touch normal-mode output needs no action here -
`baseline_diff.js` passes silently. A PR that does (e.g. a shared-template
change) will touch many files under `playwright/baseline/html/` at once,
since every sample entry's captured HTML includes the changed markup -
expect a large-file-count, easy-to-skim diff, not something to review
line-by-line. By convention, attach a representative before/after
screenshot to the PR description for the visual check GitHub hosts
PR-description images on its own CDN, not as repo blobs, so this costs
nothing in git size.

## Running the gates manually

Requires the app up against `poradnia_a11y` (`make wcag-baseline` does
this, or do it by hand - see `docker-compose.a11y.yml`'s own usage
comment) and `A11Y_SEED_PASSWORD` set to whatever value seeded it:

```bash
cd playwright
export A11Y_SEED_PASSWORD="..."
node equivalence_test.js
node axe_run.js --mode=wcag
node baseline_diff.js
node validate_html.js   # html-validate against the baseline HTML, not a CI gate
```
