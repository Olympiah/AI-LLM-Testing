# [SOURCE CITATION] Source links are shown under "I don't know" answers

**ID:** BUG-001
**Status:** Open
**Frequency:** Always (3 of 3 runs on each of 2 questions)

## Severity / Priority

**Assigned:** Medium. The chatbot assistant refuses correctly, so no wrong answer is given, but the links under the refusal suggest that the answer is in those documents. A user has no way to tell that the links are unrelated, so the citations cannot be trusted. Risk map R2 (Source citation), score 16.

## Description
The chatbot assistant answers questions from a knowledge base of five documents (three Wikipedia pages, the National Payment System Act and the National Payment System Regulations, 2014). Under every answer it shows links to the documents the answer came from.

When the question cannot be answered from the knowledge base, the chatbot assistant correctly replies "I don't know." but still shows source links. The links are the documents of the four text chunks that the search found closest to the question. There is no check on whether those chunks are relevant, so they appear even for a question that has nothing to do with the documents, such as the capital of France.

## Steps to Reproduce
1. Start the chatbot assistant locally (`npm run dev` in `chatbot/`).
2. Ask: "What is Fuliza's interest rate?"
3. Read the answer and the source links shown under it.
4. Ask: "What is the capital of France?" and read the answer and the links again.

The same check runs automatically as test MP-041 and test MP-045 (promptfoo, 3 runs each).

## Actual Result
- "What is Fuliza's interest rate?" gives the answer "I don't know." with three links: the M-Pesa Wikipedia page, the Central Bank of Kenya Wikipedia page and the Regulations PDF.
- "What is the capital of France?" gives the answer "I don't know." with one link: the Regulations PDF.
- The answer and the links were identical in all 3 runs of both questions.

## Expected Result
No source links when the answer is "I don't know". The links exist to show where an answer came from, so a link should appear only when the document supports the answer. This is the pass criteria of tests MP-041 to MP-046 and the source attribution target (90%) in the quality gate.

## Environment
- System under test: chatbot assistant version 1 (baseline), running locally.
- Models: gpt-4o-mini (temperature 0) and text-embedding-3-small, with the Pinecone index `mpesa-assistant` (245 chunks, 4 chunks retrieved per question).
- Test tool: promptfoo 0.125.1 on Node v24.21.0.
- OS: Windows.

## Root Cause Analysis
The `links` field returned by `chatbot/app/api/chat/route.ts` is built from the source of every retrieved chunk (the unique `metadata.source` of all `sourceDocuments`). The retriever always returns the 4 closest chunks, and there is no relevance threshold, so some chunks are returned for any question. Nothing clears the links when the answer is "I don't know". The console log confirms the retrieval side: an unrelated chunk was returned for an M-Pesa question.

## Recommended Fix
In version 2, filter the retrieved chunks by a relevance score (`similaritySearchWithScore` with a `MIN_SCORE`, tuned on a set of in-scope and off-topic questions so good chunks are not dropped). Show only the sources of chunks that pass the filter, and show none when nothing passes or the answer is "I don't know."

Regression tests: MP-041 to MP-046 (links must be empty on refusals), plus a check on the answerable tests that the links contain no unrelated source.
