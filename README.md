# Testing an M-Pesa and Kenya payments chatbot assistant

I built an evaluation suite around a retrieval-augmented chatbot assistant that answers questions about M-Pesa and the rules mobile-money providers must follow in Kenya. I wrote the risk map and test plan, built a ground-truth set checked against the original documents, wrote 65 test cases, ran them against the original chatbot assistant (version 1), found and documented the failures, fixed part of it (version 2), and ran the same tests again. A small automated check (the smoke gate) now runs on pull requests in GitHub Actions.

The chatbot assistant is the system under test. The testing work is the project. It uses Next.js, LangChain, OpenAI (gpt-4o-mini to answer, text-embedding-3-small to embed) and a Pinecone vector index.

## Results

Every test runs 3 times and counts as a pass only if all 3 runs pass.

| | Version 1 | Version 2 |
|---|---|---|
| Tests passing | 47 | 58 |
| Tests failing | 17 | 6 |
| Skipped (an observation, not scored) | 1 | 1 |
| Regressions | | none |

Version 2 fixed 11 of the 17 failures: source links shown under answers that do not use the knowledge base (BUG-001) and the page's opening greeting polluting the first search (BUG-004). It did not fix the two retrieval and omission bugs (BUG-002, BUG-003), which stay open with their evidence. Answer correctness did not change, because version 2 changed how the chatbot assistant answers and shows links, not what the search finds.

### Quality gate

The targets were set before the first run.

| Target | Definition | Version 1 | Version 2 | Met in version 2 |
|---|---|---|---|---|
| Answer correctness, 85% | The 40 answerable fact and rule tests, all 3 runs passing | 35 of 40 (87.5%) | 35 of 40 (87.5%) | Yes |
| Source attribution, 90% | The 43 tests that assert an expected source link, all 3 runs passing | 40 of 43 (93.0%) | 39 of 43 (90.7%) | Yes, by one test |
| Faithfulness, 90% | Answered tests scoring 0.9 or higher (gpt-4o as the judge, one run) | not computed | 36 of 38 (94.7%) | Yes |
| Abstention, 95% | The 6 near-topic and off-topic refusal tests, all 3 runs passing | 0 of 6 | 6 of 6 | Yes |
| Successful attacks, 0 | The 7 attack and robustness tests; a test counts if any run failed | 0 | 0 | Yes |

These five targets need the full suite and the score-based metrics, which cost more and vary between runs, so I check them by hand and they are not part of the automated smoke gate below. The full method, the findings, and the limits of my own evaluation are in [docs/04-evaluation-report.md](docs/04-evaluation-report.md).

## What is in this repository

| Path | What it holds |
|---|---|
| [chatbot/](chatbot/) | The chatbot assistant (Next.js app), with its own [README](chatbot/README.md) |
| [ingest/](ingest/) | The script that fetches the source documents, chunks them, embeds them and uploads them to Pinecone |
| [evals/](evals/) | The promptfoo test suites: the main suite (66 entries) and the metrics run on the 40 answerable tests |
| [docs/01-risk-map.md](docs/01-risk-map.md) | The risks, scored by impact and likelihood |
| [docs/02-test-plan.md](docs/02-test-plan.md) | Scope and test strategy |
| [docs/03-ground-truth.md](docs/03-ground-truth.md) | The question and answer pairs, each with its source and section |
| [docs/04-evaluation-report.md](docs/04-evaluation-report.md) | Method, results before and after, quality gate, findings, limits, next steps |
| [docs/sources.md](docs/sources.md) | The five knowledge base sources, their licences and known text faults |
| docs/Assistant_ Test Cases.xlsx | The 65 test cases with Status (v1) and Status (v2) side by side |
| [bug-reports/](bug-reports/) | BUG-001 to BUG-004, each with a version 2 retest |
| [.github/workflows/smoke-gate.yml](.github/workflows/smoke-gate.yml) | The smoke gate |

## How to run it

You need Node, an OpenAI key, a Pinecone account, and Python for the ingestion script. On Windows I run Python as `py`. Keys go in your terminal or in a local `.env` file that is never committed.

**1. Build the knowledge base (once).** Create a serverless Pinecone index with dimension 1536 and the cosine metric, then from the repository root:

```
py ingest/ingest.py fetch
py ingest/ingest.py upload
```

`fetch` downloads and cleans the five sources into `data/raw/`, which is gitignored. `upload` chunks, embeds and uploads them, and replaces all vectors in the index.

**2. Start the chatbot assistant.** Copy `chatbot/.env.example` to `chatbot/.env` and fill in `OPENAI_API_KEY`, `PINECONE_API_KEY` and `PINECONE_INDEX`. Then, from `chatbot/`:

```
npm install
npm run dev
```

It listens on http://localhost:3000. The tests call `POST /api/chat` on that address.

**3. Run the tests.** With the chatbot assistant running, export `OPENAI_API_KEY` in the terminal (the rubric checks and the metrics call OpenAI), then from `evals/`:

```
npm ci
npx promptfoo eval -c promptfooconfig.yaml --no-cache --repeat 3 -o results.json
npx promptfoo eval -c promptfooconfig.metrics.yaml --no-cache --repeat 1 -o results-metrics.json
```

The first command is the main suite, with 3 runs per test. The second is the metrics run (faithfulness, factuality, context recall). Every test calls the real model, so use a key with a spend limit. The metrics run costs roughly 50 cents. Results files are gitignored.

To run only some tests, filter on the test description. Every description starts with its ID, so this runs just two tests:

```
npx promptfoo eval -c promptfooconfig.yaml --filter-pattern "^(MP-001|MP-041)\b" --repeat 1 --no-cache
```

## The smoke gate

The smoke gate is a quick automated check that the chatbot assistant still behaves. It is not the quality gate above: it runs 13 tests once each and does not compute the five targets.

**What it does.** On the GitHub runner it installs the dependencies, builds and starts the chatbot assistant, waits until it answers, runs the 13 tests with promptfoo, and stops. If a test fails, only the failed tests are re-run once, because model answers can vary. A test that still fails turns the gate red. A test that fails once and passes on the re-run is reported as a warning and counts as a pass. The results are uploaded as an artifact for 7 days.

**The 13 tests.** They cover facts from different sources, refusals, the plain-check attack tests and the greetings:

| Area | Tests |
|---|---|
| Facts and rules | MP-001 (what PESA means), MP-014 (when Safaricom was formed), MP-020 (when the Central Bank of Kenya was founded), MP-024 (penalty for operating without authorisation), MP-029 (time to resolve a complaint) |
| Follow-up with history | MP-037 (resolves "that authorisation" from the earlier message) |
| Refusals, with no source links | MP-041 (Fuliza interest rate), MP-042 (current daily limit), MP-045 (capital of France) |
| Attacks and robustness | MP-047 (system prompt request), MP-051 (empty question), MP-053 (SQL and HTML as plain text) |
| Greeting with history | MP-065 (short greeting, no summary, no links) |

Eleven of them use plain text checks only. MP-047 and MP-065 also have a model-graded rubric check. The two refusal checks on links protect the version 2 fix for BUG-001.

**When it runs.** On pull requests into `main` that change `chatbot/`, `evals/` or `.github/workflows/`, and on demand. Changes to docs, the workbook or this README do not start a run, and there is no run on every push, because every test costs money. To run it by hand, open the Actions tab, choose "Smoke gate", then "Run workflow". The optional "pattern" box takes a regex on test descriptions, so I can run a different set. I checked that the gate can fail by running it on a test that is known to fail (MP-003), and it went red.

**Keys.** Add three repository secrets in the GitHub settings: `OPENAI_API_KEY`, `PINECONE_API_KEY` and `PINECONE_INDEX`. The build and start steps get all three. The test step gets only the OpenAI key. The keys are never in the repository, and the workflow does not read `chatbot/.env`. Ingestion is not run in CI: the Pinecone index already exists.

## Known limits

- The judge model varies, so I do not read a movement of a single test as a real change. The metrics run is a one-run trial.
- Version 1 and version 2 are not an identical-config comparison, because I corrected some checks between version 1 runs.
- The National Payment System Act in the knowledge base is the 2011 text as originally enacted, so it is not a current legal reference. The Wikipedia pages are snapshots, and two of them disagree on some facts.
- Safaricom's site and Kenya Law block automated access, so I did not use them and did not try to get around the blocks.

The full list is in section 10 of the evaluation report.

## Credit and licences

**Wikipedia text.** The knowledge base includes text from the English Wikipedia articles [M-Pesa](https://en.wikipedia.org/wiki/M-Pesa), [Safaricom](https://en.wikipedia.org/wiki/Safaricom) and [Central Bank of Kenya](https://en.wikipedia.org/wiki/Central_Bank_of_Kenya), written by their contributors (see each article's history for the authors). That text is available under the [Creative Commons Attribution-ShareAlike licence (CC BY-SA)](https://creativecommons.org/licenses/by-sa/4.0/). I fetched it through the Wikipedia API, cleaned it and split it into chunks, and I use short excerpts in the ground truth and the test cases. Those changes are mine. The extracted text itself is not published in this repository (`data/` is gitignored). Any text taken from Wikipedia and reused from this project stays under CC BY-SA.

**Legislation.** The National Payment System Act (No. 39 of 2011) and the National Payment System Regulations, 2014 are published by the Central Bank of Kenya. I link to the originals in [docs/sources.md](docs/sources.md) and do not publish the extracted text.
