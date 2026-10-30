# [MULTI-TURN] The page's opening greeting is mixed into the search, so a first message like "hi" gets an unrelated M-Pesa summary

**ID:** BUG-004
**Status:** Fixed in version 2
**Frequency:** Always (3 of 3 runs)

## Severity / Priority

**Assigned:** Medium. The answer is not false, but a user who says "hi" gets a long summary they did not ask for, with a source link. The page sends its opening greeting with every message, so this is what a real user triggers on a first message, and my empty-history tests could not see it. Only "hi" has been tested with the greeting so far. If other short or off-topic first messages behave the same way, the severity goes up. Risk map R6 (Follow-up questions: earlier turns confuse the answer), score 12.

## Description
The chatbot page starts with a greeting from the assistant ("Hello! Ask me about M-Pesa and Kenya's mobile-money and payment regulation…"). When the user sends a message, the page sends that greeting along as the first item of the history. Version 1 turns the history into one block of text and, because the history is not empty, rewrites the new message into a standalone question using it. For a message like "hi" the rewrite is built from the greeting, so the search and the answer are about M-Pesa and not about the greeting.

## Steps to Reproduce
1. Start the chatbot assistant locally (`npm run dev` in `chatbot/`) and open `http://localhost:3000`.
2. As the first message, send: `hi`
3. Read the answer and the source link.

To see what the page sends: open the browser developer tools (F12), click the Network tab, send `hi`, click the `chat` request and read the Payload. It is:

`{"query":"hi","history":[{"role":"assistant","content":"Hello! Ask me about M-Pesa and Kenya's mobile-money and payment regulation. I answer only from my source documents and show which one I used."}]}`

The same check runs automatically as test MP-065 (promptfoo, 3 runs), which sends `hi` with that exact history.

## Actual Result
- MP-065 (`hi` with the greeting in the history): in all 3 runs the answer was an unprompted overview of M-Pesa of about 1,500 characters (launch in 2007, 17 million subscribers, KYC, licence, a transaction figure and a paragraph on regulation). The link was the M-Pesa Wikipedia page. The answers differed slightly in wording.
- MP-061 (the same `hi` with an empty history): "Hello! How can I assist you today?" in all 3 runs. The only difference between the two tests is the history entry.

## Expected Result
A short greeting back, with no summary of M-Pesa. This is the pass criteria of MP-065: the answer is under 500 characters, and no source links are shown.

## Environment
- System under test: chatbot assistant version 1 (baseline), running locally.
- Models: gpt-4o-mini (temperature 0) and text-embedding-3-small, with the Pinecone index `mpesa-assistant` (245 chunks, 4 chunks retrieved per question).
- Test tool: promptfoo 0.125.1 on Node v24.21.0.
- OS: Windows. Browser: Chrome.

## Root Cause Analysis
Two pieces of code work together.

`chatbot/app/api/chat/route.ts`, line 13: the history is turned into one string of message contents. The roles are lost, so the chain cannot tell the greeting came from the assistant.

```ts
chat_history: history.map(h => h.content).join("\n"),
```

`conversational_retrieval_chain.js` in `@langchain/classic`, lines 143 to 152: the rewrite step runs whenever that string is not empty, and the rewritten question is what is searched.

```js
if (chatHistory.length > 0) {
    const result = await this.questionGeneratorChain.call({ question, chat_history: chatHistory }, ...);
    ...
    newQuestion = result[keys[0]];
}
const docs = await this.retriever.invoke(newQuestion, ...);
```

The rewritten question is also what the answer step receives. With an empty history the rewrite is skipped and the raw question goes to the search, which is why MP-061 gets a normal greeting.

## Recommended Fix
In version 2 before the history is turned into text, drop any assistant message that comes before the first user message, and keep the rest of the history. If nothing is left, pass an empty history so the rewrite is skipped and "hi" goes to the search as it is. Dropping all assistant messages is not recommended, because a follow-up such as "and what's the penalty for that?" needs the previous answer to know what "that" is. Stopping the page from sending the greeting is harmless as an extra, but it would not fix the API for other callers.

Regression tests: MP-065, MP-061 to MP-064, and a follow-up test (a question followed by "and for how long?") to show that real conversations still work.

## Version 2 retest

**Result:** Fixed in version 2.

MP-065 (`hi` with the page's opening greeting in the history) passed 3 of 3 runs in the full run and 5 of 5 in a separate 5-run check. The reply is a short greeting that says the chatbot assistant can answer questions about M-Pesa and Kenya's payment regulation, with no source links and no summary. In version 1 it was an overview of about 1,500 characters. The follow-up tests MP-037 and MP-038 (a question followed by a short follow-up) also passed 3 of 3 runs, so real conversations still work.

How it was fixed: before the history is turned into text, assistant messages that come before the first user message are dropped, and the rest of the history is kept with its roles ("Human: ..." and "Assistant: ..."). When nothing is left, the rewrite step is skipped and "hi" is searched as it is. The rewrite prompt also tells the chatbot assistant to leave a greeting or thanks unchanged.
