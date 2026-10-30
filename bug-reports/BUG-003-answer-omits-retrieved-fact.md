# [ANSWER COMPLETENESS] The answer leaves out a fact that was in the retrieved text

**ID:** BUG-003
**Status:** Open
**Frequency:** Always (3 of 3 runs on each of 2 questions)

## Severity / Priority

**Assigned:** Medium. Nothing in the answers is false, but each one leaves out a requirement that the knowledge base states and that the user asked about. For the complaint question the missing fact is the 30-day deadline for the provider to resolve the complaint. The closest risk map entry is R1 (answers must match the sources). It was seen in 2 of the 42 tests run so far (MP-039 and MP-040).

## Description
For some questions, the retrieved text contains the fact needed, but the chatbot assistant answers with only part of it. The answers read as complete, so a user has no way to tell that something is missing.

## Steps to Reproduce
1. Start the chatbot assistant locally (`npm run dev` in `chatbot/`).
2. Ask: "If I complain to my provider and I am not satisfied, what can I do?"
3. Ask: "What licence does a provider need, and what does the law say it must do with customer money?"
4. Read the answers.

The same questions run automatically as tests MP-039 and MP-040 (promptfoo, 3 runs each).

## Actual Result
- **MP-039:** "If you are not satisfied with the decision of your payment service provider regarding your complaint, you may appeal to the Bank." The 30-day deadline in regulation 40(1) is not mentioned. The text "thirty days" was in the second retrieved chunk.
- **MP-040:** the answer covers the licence (authorisation from the Bank, with the application documents). For customer money it describes a register of customers, identity verification and confidentiality, and does not mention the trust fund (regulation 25(3)). The text about the trust fund was in the fourth retrieved chunk.
- The answers were identical in all 3 runs of both questions.

## Expected Result
- **MP-039:** the provider must resolve the complaint within thirty days, and an unsatisfied customer may appeal to the Bank.
- **MP-040:** a provider needs authorisation (Act s.12-13) and holds customer money in a trust fund (Regulations reg 25(3)).

This is the pass criteria of MP-039 and MP-040, and it counts toward the answer correctness target (85%) in the quality gate.

## Environment
- System under test: chatbot assistant version 1 (baseline), running locally.
- Models: gpt-4o-mini (temperature 0) and text-embedding-3-small, with the Pinecone index `mpesa-assistant` (245 chunks, 4 chunks retrieved per question).
- Test tool: promptfoo 0.125.1 on Node v24.21.0.
- OS: Windows.

## Root Cause Analysis
Not confirmed yet. What is known: the fact was in the text given to the model and was left out of the answer. The version 1 prompt does not tell the model to cover every part of the question or to include all the relevant requirements. Both questions have two parts, and in MP-040 the relevant chunk was ranked last of 4. Whether the order or the wording of the prompt matters more is not yet measured. The model-graded answer relevancy and faithfulness checks, run on a subset on Saturday, will add evidence.

MP-040 also has a retrieval side (no chunk from the Act was retrieved), which is logged in BUG-002.

## Recommended Fix
In version 2, change the prompt so that the model answers every part of the question using all the relevant requirements in the text it is given, and says which part the text does not cover. Check the effect on MP-039 and MP-040, and check that it does not lead to longer answers on the questions that already pass.

Regression tests: MP-039 and MP-040, plus the answer relevancy check on the answerable tests.

## Version 2 retest

**Result:** Still open.

MP-039 still leaves out the thirty days in all 3 runs, and MP-040 still leaves out the trust fund part. The new prompt rule "answer every part of the question, and say which part the sources do not cover" did not fix either answer. MP-040 does not say that the trust fund part cannot be answered. The MP-040 answer varied between runs: the trust-fund wording appeared in one earlier version 2 run and not in the final run.
