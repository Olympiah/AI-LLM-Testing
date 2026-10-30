# [RETRIEVAL] The chunk that holds the answer is not among the 4 retrieved, so the chatbot assistant says "I don't know" or answers incompletely

**ID:** BUG-002
**Status:** Open
**Frequency:** Always (3 of 3 runs on each of 3 questions)

## Severity / Priority

**Assigned:** High. The answer is in the knowledge base and the question is in scope, but the chatbot assistant says "I don't know." to two of the three questions and gives an incomplete answer to the third. A user cannot tell that the answer exists. Risk map R5 (Retrieval quality), score 12 in the risk map. It was seen in 3 of the 42 tests run so far (MP-003, MP-008, MP-035).

## Description
The chatbot assistant finds the 4 chunks of text closest to the question and answers only from those. For some in-scope questions, the chunk that contains the answer is not among those 4. The model then says "I don't know." (it was only given unrelated text) or answers with only part of the facts.

I checked that the text exists in the knowledge base. It is there. It was not retrieved.

## Steps to Reproduce
1. Start the chatbot assistant locally (`npm run dev` in `chatbot/`).
2. Ask: "What did a group of banks lobby for in December 2008, and what happened?"
3. Ask: "How must a provider verify a customer's identity card or passport?"
4. Ask: "In which countries were M-PESA rollouts terminated because of low uptake?"
5. Read each answer and the links under it.

The same questions run automatically as tests MP-008, MP-035 and MP-003 (promptfoo, 3 runs each).

## Actual Result
- **MP-008:** the answer is "I don't know." The links are the Central Bank of Kenya Wikipedia page, the Regulations PDF and the Act PDF. None of them is the M-Pesa page that holds the answer.
- **MP-035:** the answer is "I don't know." The link is the Regulations PDF, which is the right document, but the chunk with the answer was not retrieved.
- **MP-003:** the answer names Romania (December 2017) and Albania (14 July 2017) and leaves out India.
- The answers were identical in all 3 runs of all three questions.

Evidence that the text exists but was not retrieved:
- "audit" and "the audit found that the service was robust" are in the cleaned M-Pesa Wikipedia text. "Integrated Population Registration System" is in the cleaned Regulations text (regulation 12(2)). Neither phrase appears in any of the 4 retrieved chunks, even with spaces ignored (checked in `results-v1-42.json`).
- For MP-003, the third retrieved chunk ends with the heading `=== India ===`. The text under that heading is in the next chunk, which was not retrieved, so the chunk boundary falls right after the heading.

## Expected Result
The chunk that holds the answer is retrieved, and the chatbot assistant gives the full answer from it. These are the pass criteria of MP-003, MP-008 and MP-035, and they count toward the answer correctness target (85%) in the quality gate.

## Environment
- System under test: chatbot assistant version 1 (baseline), running locally.
- Models: gpt-4o-mini (temperature 0) and text-embedding-3-small, with the Pinecone index `mpesa-assistant` (245 chunks of about 1,000 characters with 150 overlap, 4 chunks retrieved per question).
- Test tool: promptfoo 0.125.1 on Node v24.21.0.
- OS: Windows.

## Root Cause Analysis
Not confirmed yet. What is known: the retriever returns the 4 chunks with the highest similarity to the question and nothing else (no reranking, no larger candidate set). Overlapping chunks from one section can take several of the 4 places, and chunks are cut at fixed lengths, so a heading can end up in a different chunk from its text (MP-003). Which of these causes applies to each question is not yet measured. The model-graded context recall check will show it.

MP-040 ("What licence does a provider need, and what does the law say it must do with customer money?") may have the same cause. No chunk from the Act was retrieved, and the trust-fund text only appeared in the fourth chunk. It is also logged in BUG-003.

## Recommended Fix
Not decided. Version 2 is planned to filter retrieved chunks by a relevance score, but a filter only removes chunks and cannot bring back one that was never retrieved. The options to compare after the context recall results:
- retrieve more candidate chunks (for example 8 to 10), then filter them by score;
- split the documents at section headings so that a heading stays with its text;
- ask the model to treat a multi-part question as separate searches.

Regression tests: MP-003, MP-008, MP-035 and MP-040, plus the context recall check on the answerable tests.

## Version 2 retest

**Result:** Still open. Retrieval was not changed in version 2.

MP-008 and MP-035 answer "I don't know based on my sources." in all 3 runs. MP-055 (the Swahili complaint question) does the same, and it is also recorded as a Swahili limitation. MP-003 still leaves out India. MP-040 still has no link to the Act. These are the same retrieval misses as in version 1, because the search still returns the 4 closest chunks, with no change to the chunks, their size or the number retrieved.

What changed is only the surface: the refusal wording, and the fact that a refusal now shows no source links.
