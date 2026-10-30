# Evaluation report: M-Pesa and payment-regulation chatbot assistant

I tested a retrieval-augmented chatbot assistant that answers questions about M-Pesa and the rules mobile-money providers must follow in Kenya. I treated it as a black box, wrote 65 test cases, ran them against the original chatbot assistant (version 1), recorded what failed and why, fixed part of it (version 2), and ran the same tests again.

This report gives the method, the results before and after, the quality gate, the findings, the limits of my own evaluation, and what I would do next.

## 1. Summary

- **Version 1 baseline:** 47 tests Pass, 17 Fail, 1 Skipped (an observation that is not scored). Every test gave the same verdict in all 3 runs.
- **Version 2:** 58 Pass, 6 Fail, 1 Skipped. 11 of the 17 failures are fixed and there are no regressions: every version 2 failure was already a version 1 failure.
- **What was fixed:** source links shown under answers that do not use the knowledge base (BUG-001), and the page's opening greeting polluting the first search (BUG-004).
- **What was not fixed:** the chunk with the answer is sometimes not retrieved (BUG-002) and the chatbot assistant sometimes leaves out a fact it was given (BUG-003). I did not change retrieval, and a prompt rule did not fix the omissions. These stay open with their evidence.
- **Quality gate:** all five targets are met in version 2, source attribution by one test (section 6).
- **One result that did not change:** answer correctness is 35 of 40 in both versions. Version 2 improved links, refusals and greetings, not the facts.

| Quality target | Version 1 | Version 2 | Target |
|---|---|---|---|
| Answer correctness | 87.5% (35 of 40) | 87.5% (35 of 40) | 85% |
| Source attribution | 93.0% (40 of 43) | 90.7% (39 of 43) | 90% |
| Faithfulness (answered tests) | not computed | 94.7% (36 of 38) | 90% |
| Abstention | 0 of 6 | 6 of 6 | 95% |
| Successful attacks | 0 | 0 | 0 |

## 2. What I tested

**The system.** A Next.js chatbot assistant with a single endpoint, `POST /api/chat`, which takes a question and the conversation history and returns the answer, the source links and the retrieved text chunks. It uses gpt-4o-mini (temperature 0) to write answers, text-embedding-3-small to embed text, and a Pinecone index of 245 chunks (about 1,000 characters each, 150 overlap). The search returns the 4 closest chunks, with no relevance cut-off and no reranking. Version 1 has no prompt of its own: it runs on LangChain's default prompts.

**The knowledge base (5 sources).** The Wikipedia pages on M-Pesa, Safaricom and the Central Bank of Kenya, and the National Payment System Act and the National Payment System Regulations, 2014, read from the Central Bank's PDFs. The Act in the knowledge base is the 2011 text as originally enacted, so it is not a current legal reference. Kenya Law and Safaricom's site block automated access, so I did not use them.

**The tests.** 65 test cases in 12 sections, in `docs/Assistant_ Test Cases.xlsx`. Each has a risk reference, an expected answer, the source it comes from and pass criteria.

| Section | Tests |
|---|---|
| Facts: M-Pesa | 13 |
| Facts: Safaricom | 6 |
| Facts: Central Bank of Kenya | 3 |
| Rules: National Payment System Act | 6 |
| Rules: National Payment System Regulations | 8 |
| Follow-ups and multiple documents | 4 |
| Refusals: near-topic and off-topic | 6 |
| Attacks and robustness | 7 |
| Swahili and mixed language | 3 |
| Bias pairs | 2 |
| Outdated or conflicting sources | 2 |
| Greetings and conversation history | 5 |

The expected answers for the first 40 tests (facts and rules) were checked against the original PDFs and pages, not only against the extracted text. The risks the tests cover are in `01-risk-map.md`, scored by impact and likelihood, and the strategy is in `02-test-plan.md`.

## 3. How I ran and measured

**The tool.** promptfoo, calling `POST /api/chat` as a black box. Each test runs 3 times and passes only if all 3 runs pass, because the chatbot assistant can answer differently on the same question. A test that gives different verdicts in different runs is counted as unstable.

**Three kinds of check, cheapest first.**
1. **Plain text checks** (JavaScript): whether the answer contains the expected fact, whether the source links include the expected page, whether the links are empty, how long the answer is. These are fast and free, but brittle when written as patterns on free text.
2. **Rubric checks** (a model reads the answer and applies a written rule): used for the attack, bias and greeting tests, where the pass condition is a judgement. The judge is gpt-4o-mini at temperature 0, and it sees only the answer text.
3. **Score-based metrics** (gpt-4o as the judge, run as a separate evaluation on the 40 answerable tests, one run each): faithfulness, factuality and context recall. I measured answer relevance and context relevance too and dropped them.

**Cost.** Every test calls the real model. The metrics run on 40 tests uses about 140,000 tokens, roughly 50 cents. A separate test key with a spend limit was used throughout.

## 4. How to read the results

- **Pass or Fail in the workbook:** a test is Pass only if all 3 runs pass. Status (v1) is the frozen baseline on the original chatbot assistant and Status (v2) is the result on version 2. They sit side by side so the baseline is never overwritten.
- **Faithfulness** asks whether every statement in the answer is supported by the retrieved chunks. It is reported on answered tests only, because the grader cannot score a bare "I don't know" and returns a parse failure.
- **Factuality** compares the answer with my expected answer and puts it in one of five categories. A "subset" (the answer is correct but leaves out part of the expected answer) counts as consistent and passes. So factuality hides omissions, which the plain checks catch (for example MP-003).
- **Context recall** asks whether the retrieved chunks contain what the expected answer says. It is unreliable when the expected answer is one or two words, or an instruction instead of a fact (MP-016, MP-033, MP-038), so I use it as a hint about retrieval, not as a gate.
- **Rubric checks see only the answer text.** My first run let the judge see the whole API response, including the retrieved chunks, and it called a refusal a reproduction of the sources.
- **The judge varies.** The same answer got different scores or verdicts in different runs (section 8), so I do not read a movement of one test as a real change. The metrics run uses one run per test, so I present it as a trial.

## 5. Version 1 baseline

Version 1 passed 47 and failed 17. The failures fall into four groups, each written up as a bug report in `bug-reports/`:

| Bug | What happens | Tests |
|---|---|---|
| BUG-001 | Source links are shown under answers that do not use the knowledge base: refusals, greetings, "I don't know" | MP-041 to MP-046, MP-061 to MP-064 |
| BUG-002 | The chunk with the answer is not among the 4 retrieved, so the chatbot assistant says "I don't know" or gives a partial answer | MP-003, MP-008, MP-035, part of MP-040 |
| BUG-003 | A fact that was retrieved is left out of the answer | MP-039, part of MP-040 |
| BUG-004 | The page's opening greeting is joined to the user's first message before the search, so "hi" returns a long M-Pesa summary | MP-065 |

MP-055 (a Swahili question) also fails, and the data protection and "who launched M-PESA" tests are not bugs. I recorded them as limitations and source disagreements.

## 6. Version 2 changes and results

**What I changed (Part 1).**
- A prompt written for this chatbot assistant: answer only from the context, say "I don't know based on my sources." when it is not there, answer every part of the question, say when sources disagree, reply briefly to a greeting, ask what the user wants for a vague message, refuse to reveal instructions.
- History handling: the opening assistant greeting is dropped before the first user message, and the rest of the history keeps its roles. The rewrite step leaves a greeting or thanks unchanged.
- The question-and-answer chain from the legacy LangChain package is replaced by plain steps (rewrite, search, answer) with the same request and response shape.
- Source links come from a field in a structured reply that says whether the answer used the knowledge base.
- The page shows the "Sources:" label only when there is at least one link.

**What I did not change.** The index, the data, the chunks, the models and the retrieval (4 chunks, no cut-off). I did not implement a retrieval fix.

**Results.**

| Run | Version 1 | Version 2 |
|---|---|---|
| Tests passing all 3 runs (workbook basis, 65 tests) | 47 Pass, 17 Fail, 1 Skipped | 58 Pass, 6 Fail, 1 Skipped |
| Runs passing, full suite (66 config entries, 3 runs each) | not comparable | 180 of 198, 0 errors, 0 unstable |
| Fixed | | MP-041 to MP-046, MP-061 to MP-065 |
| Regressions (a test that passed in version 1 and fails in version 2) | | none |

One link check did go from pass to fail (MP-035, source attribution). It was a pass by accident in version 1, where a link was shown under "I don't know", and the test itself was already failing (section 7).

All 33 runs on the refusal and greeting tests now have no links, where every one had 1 to 3 links in version 1. The version 1 results come from several runs on different config versions, because I corrected checks between runs, so this is not an identical-config comparison.

**By section** (Pass / Fail, version 1 then version 2):

| Section | Version 1 | Version 2 |
|---|---|---|
| Facts: M-Pesa | 11 / 2 | 11 / 2 |
| Facts: Safaricom | 6 / 0 | 6 / 0 |
| Facts: Central Bank of Kenya | 3 / 0 | 3 / 0 |
| Rules: National Payment System Act | 6 / 0 | 6 / 0 |
| Rules: National Payment System Regulations | 7 / 1 | 7 / 1 |
| Follow-ups and multiple documents | 2 / 2 | 2 / 2 |
| Refusals: near-topic and off-topic | 0 / 6 | 6 / 0 |
| Attacks and robustness | 7 / 0 | 7 / 0 |
| Swahili and mixed language | 2 / 1 | 2 / 1 |
| Bias pairs | 2 / 0 | 2 / 0 |
| Outdated or conflicting sources | 1 / 0 (1 skipped) | 1 / 0 (1 skipped) |
| Greetings and conversation history | 0 / 5 | 5 / 0 |

**Score-based metrics** (gpt-4o as the judge, run as a separate evaluation on the 40 answerable tests, one run each):

| Metric | Version 1 | Version 2 |
|---|---|---|
| Factuality | 36 of 40 | 35 of 40 |
| Faithfulness at 0.9 or higher (answered tests, 38) | 35 of 38 | 36 of 38 (94.7%) |
| Mean faithfulness (answered tests) | 0.965 | 0.974 |
| Mean context recall (all 40) | 0.875 | 0.812 |

The metrics are essentially unchanged, which is expected: version 2 changed how the chatbot assistant answers and shows links, not what the search finds, and these tests are all answerable questions. The small differences come from the judge's variation and from one real retrieval signal (MP-023, section 8).

## 7. Quality gate

The targets were set before the first run: answer correctness 85%, source attribution 90%, faithfulness 90%, abstention 95%, 0 successful attacks. I fixed the definitions below before counting.

| Target | Definition | Version 1 | Version 2 | Met in version 2 |
|---|---|---|---|---|
| Answer correctness, 85% | The 40 answerable fact and rule tests; a test counts only if all 3 runs pass | 35 of 40 (87.5%) | 35 of 40 (87.5%) | Yes |
| Source attribution, 90% | The 43 tests that assert an expected source link, passing in all 3 runs | 40 of 43 (93.0%) | 39 of 43 (90.7%) | Yes, by one test |
| Faithfulness, 90% | Answered tests at 0.9 or higher | not computed | 36 of 38 (94.7%) | Yes |
| Abstention, 95% | The 6 near-topic and off-topic refusal tests, whole test passing in all 3 runs | 0 of 6 | 6 of 6 | Yes |
| Successful attacks, 0 | The 7 tests in "Attacks and robustness"; a test counts if any run failed | 0 | 0 | Yes |

Reported separately, with no target: the 11 tests that assert no links went from 0 of 11 to 11 of 11, and false refusals (an answerable question answered with "I don't know") are 3 of 43 in both versions (MP-008, MP-035, MP-055). The abstention figure does not count false refusals, so I state them here.

How I read these numbers:
- **Correctness did not change.** The same five tests fail in both versions (MP-003, MP-008, MP-035, MP-039, MP-040).
- **Attribution went down by one test because of the fix.** In version 1, MP-035 passed its link check by accident: it said "I don't know." and still showed a link to the Regulations. In version 2 it correctly shows no link, so the check fails. Version 2 clears the target by exactly one test.
- **Version 1's abstention failure was about links, not wording.** All six refusals said the right thing and showed source links.

## 8. Findings

**Bugs fixed in version 2**
- **BUG-001, source links under non-answers.** MP-041 to MP-046 and MP-061 to MP-065 pass 3 of 3, and none of the 33 runs shows a link. My first fix, a text marker in the prompt, was applied backwards in 7 of 7 manual checks, so I replaced it with a structured field. That field then needed its own fix: it treated partial answers as not using the sources, so MP-052 and MP-058 lost their links, and its wording was corrected.
- **BUG-004, the opening greeting in the search.** MP-065 passes 3 of 3 in the full run and 5 of 5 in a separate check. In version 1, "hi" returned an overview of about 1,500 characters.

**Bugs still open**
- **BUG-002, the answer chunk is not retrieved.** MP-008, MP-035 and MP-055 answer "I don't know based on my sources." in all 3 runs, MP-003 still leaves out India, and MP-040 still lacks the link to the Act. The text is in the knowledge base but not among the 4 retrieved chunks. MP-057 (the bias pair) shows how sensitive the search is: changing only a person's name changed which chunks came back.
- **BUG-003, a retrieved fact is left out.** MP-039 still leaves out the thirty days, and MP-040 still leaves out the trust-fund part. The prompt rule "answer every part of the question" did not fix either, and the MP-040 answer varies between runs.

**Observations and limitations (not bugs)**
- **Swahili questions** (MP-055): the knowledge base is English and nothing states Swahili support. The two other Swahili tests pass because they share words with the English text.
- **The sources disagree** on data protection law (MP-059) and on who launched M-Pesa (MP-002): one Wikipedia page says "Vodafone and Safaricom" and another says "Vodafone for Safaricom and Vodacom", and the chatbot assistant repeats whichever it retrieved. The prompt rule to say when sources disagree did not make it say so on MP-002.
- **Source links show all retrieved sources**, not only the ones the answer used, so a partial answer can show a link that covers only the part it could not answer.
- **A right answer from an indirect source (MP-023).** The chunks retrieved for "How long is a payment service provider authorisation valid?" hold only the renewal clause, not the validity rule. The chatbot assistant reached "twelve months" by inference, the plain check passes because the number is right, and context recall scored 0.00. This is the same fragility as BUG-002.
- **A small inference (MP-001).** Faithfulness fell from 1.00 to 0.67 because the answer added "Therefore, M-PESA stands for 'mobile money'", which the sources do not state.

## 9. Problems in my own tests

Several first-run failures were defects in my checks, not in the chatbot assistant. I fixed the check each time and kept the original run:
- Six plain checks asked for more than the question required or for one exact wording.
- A rubric judge was given the retrieved chunks next to a refusal and called it a reproduction.
- The first bias-pair questions did not ask for the deadline the test expected.
- The greeting rubric failed a correct reply because it mentioned M-Pesa, which my own prompt rule asks for. It was reworded twice with the same ground truth, and then passed 15 of 15 runs.
- A plain check on MP-047 looked for phrases from LangChain's default prompt, which version 2 does not contain, so it could not fail. It now looks for two phrases that exist only in the version 2 prompt.
- A suspected defect on MP-002 turned out, after reading the retrieved chunks, to be a disagreement between two sources, so I did not add a check.

## 10. Limits of this evaluation

- **The judge varies.** The same answer got different scores (MP-003: 0.67, 0.00, 0.50 on the same chunks and answer text), and the same text passed and failed factuality (MP-002, MP-023). The cheap rubric judge was unstable on a borderline case (MP-065) until I made the rule explicit. Single-test movements are not read as real changes.
- **The metrics are a one-run trial** on 40 tests, so they carry that noise. Three parse or format problems occurred: faithfulness could not score bare refusals (MP-008, MP-035) and recall returned a format error on a correct answer (MP-037).
- **Version 1 and version 2 are not an identical-config comparison**, because I corrected checks between version 1 runs.
- **Five of the five repeated runs on three tests** is a small sample: I say the greeting tests are stable in 5 of 5, not fixed for good.
- **The Act is the 2011 original**, so some rules may since have changed. Wikipedia snapshots are a weak source for facts that change.
- **The extracted PDF text has small OCR errors** and margin headings inside sentences, so I checked every number, date and amount against the original PDF.
- **13 npm vulnerabilities** in old dependencies were left unfixed on purpose, to keep the baseline unchanged.

## 11. What I would do next

1. **Retrieval (BUG-002).** Retrieve about twelve candidate chunks instead of 4, filter them by similarity score, and keep up to six. A filter on the top 4 would only remove chunks and would not bring back a missing one. Check the Pinecone index's metric first (cosine and dot product keep high scores, euclidean keeps low scores), and set the cut-off from logged scores for all the test questions. Add reranking only if context recall still shows a problem. The tests that would verify it are MP-003, MP-008, MP-035, MP-055, MP-040, MP-057 and the context recall metric. Splitting the text at regulation boundaries would help chunks cut mid-sentence, such as MP-035's.
2. **Omissions (BUG-003).** A completeness check on each answer would add a model call to every question, so I would try it only if omissions matter to the product.
3. **Source attribution.** Have the model say which source it used for each fact, so the links show only those.
4. **A stronger judge** for the rubric checks, and repeated metric runs to measure the judge's variation directly.
5. **Swahili.** Translate the question before the search, which needs its own tests.

## 12. Where things are

| File | What it holds |
|---|---|
| `docs/01-risk-map.md` | The risks, scored by impact and likelihood |
| `docs/02-test-plan.md` | Scope and strategy |
| `docs/03-ground-truth.md` | The question and answer pairs, with sources |
| `docs/Assistant_ Test Cases.xlsx` | The 65 test cases with Status (v1) and Status (v2) |
| `docs/sources.md` | The knowledge base sources, licences and known text faults |
| `bug-reports/` | BUG-001 to BUG-004, each with a version 2 retest |
| `evals/promptfooconfig.yaml` | The main test suite (66 entries) |
| `evals/promptfooconfig.metrics.yaml` | The metrics run on the 40 answerable tests |

The results files are not in the repository (they are ignored by `.gitignore`). To reproduce a run, start the chatbot assistant, export an OpenAI key in the terminal, and run, from `evals/`:

```
npx promptfoo eval -c promptfooconfig.yaml --no-cache --repeat 3 -o results.json
npx promptfoo eval -c promptfooconfig.metrics.yaml --no-cache --repeat 1 -o results-metrics.json
```
