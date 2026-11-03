// Regression gate for the full suite.
//
// WHY THIS EXISTS: the full suite has a few tests that fail on purpose-known
// bugs (for example BUG-002). If CI went red on every failure, it would always
// be red and people would learn to ignore it. So instead of "any failure =
// red", this script uses "any NEW failure = red": a failure that is not on the
// known list. Known bugs are tracked in the bug reports, not by the gate.
//
// USAGE:  KNOWN_FAILURES="MP-003,MP-008" node check-regressions.js results.json
//   argv[2]               path to the promptfoo results JSON file
//   KNOWN_FAILURES (env)  comma-separated test IDs that are allowed to fail
//
// EXIT CODE: 1 if a test outside the known list failed, otherwise 0. CI reads
// this exit code to turn the job red or green.

const fs = require("fs");

// The results file path is the first command-line argument after "node script".
const file = process.argv[2];

// Turn "MP-003, MP-008" into a Set of IDs. A Set gives fast "is it known?"
// lookups. trim() removes stray spaces and filter(Boolean) drops empty strings
// (for example when the variable is unset or has a trailing comma).
const known = new Set(
  (process.env.KNOWN_FAILURES || "").split(",").map((s) => s.trim()).filter(Boolean)
);

const data = JSON.parse(fs.readFileSync(file, "utf8"));

// Different promptfoo versions nest the rows differently, so try the common
// shapes in order: data.results.results, then data.results, then an empty list.
// "?." and "??" avoid crashing when a level is missing.
const rows = data.results?.results ?? data.results ?? [];

// Group the rows by test ID. The full suite runs each test several times
// (--repeat 3), so one test produces several rows.
const byId = new Map();
for (const r of rows) {
  const desc = r.testCase?.description ?? r.description ?? "";
  // Every description starts with its ID, e.g. "MP-001 Verify ...".
  const m = desc.match(/^(MP-\d+)/);
  if (!m) continue; // ignore rows that are not one of our tests
  const id = m[1];
  // STRICT RULE: a test counts as passed only if EVERY run of it passed.
  // "(previous ?? true) && this run's result" starts at true and flips to
  // false forever on the first failed run. So a flaky test (2 of 3 passes) is
  // treated as a failure, not hidden by the passes.
  byId.set(id, (byId.get(id) ?? true) && r.success === true);
}

const passed = [...byId].filter(([, ok]) => ok).map(([id]) => id);
const failed = [...byId].filter(([, ok]) => !ok).map(([id]) => id);

// Three groups that matter for the report:
//   newFailures  = failed AND not known  -> a regression, makes the job red
//   stillFailing = failed AND known      -> expected, does not block
//   fixed        = passed AND known      -> a bug got fixed; remove it from the
//                                           known list so it is guarded again
const newFailures = failed.filter((id) => !known.has(id));
const fixed = passed.filter((id) => known.has(id));
const stillFailing = failed.filter((id) => known.has(id));

// Markdown report. GitHub renders it on the run's summary page.
const lines = [
  "## Full suite result",
  "",
  `| Passed | Failed | Total tests |`,
  `|---|---|---|`,
  `| ${passed.length} | ${failed.length} | ${byId.size} |`,
  "",
  `- New failures: ${newFailures.length ? newFailures.join(", ") : "none"}`,
  `- Known failures still failing: ${stillFailing.length ? stillFailing.join(", ") : "none"}`,
  `- Known failures that now pass: ${fixed.length ? fixed.join(", ") : "none"}`,
];

const text = lines.join("\n");
console.log(text);

// GITHUB_STEP_SUMMARY is a file path that GitHub Actions provides. Appending
// markdown to it shows the report on the run page. Locally the variable is not
// set, so we only print to the console.
if (process.env.GITHUB_STEP_SUMMARY) {
  fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, text + "\n");
}

// The gate itself: a non-zero exit code makes the CI step, and so the job, go red.
if (newFailures.length > 0) {
  console.error(`New failures: ${newFailures.join(", ")}`);
  process.exit(1);
}
