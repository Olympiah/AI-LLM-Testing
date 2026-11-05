# M-Pesa Assistant: Risk Map

**System under test:** a question-answering chatbot about M-Pesa and Kenya's mobile-money and payment regulation (Next.js web app with a `POST /api/chat` endpoint, LangChain, OpenAI gpt-4o-mini, Pinecone vector search)
**Scope:** the chat API and the answers it gives. I test it as a black box through `/api/chat`.

## 1. What I checked before writing this

Findings (not assumptions):

- The app is stateless. The browser sends the new question plus the whole chat history on every request, and the server keeps nothing between requests.
- The server joins the history into one block of text. The messages are not passed with roles, so the model cannot tell which lines the user wrote and  which the assistant wrote. (verify)
- When the history is empty, the first question is searched as typed. When there is history, an extra model call first rewrites the question into a standalone one. So follow-up questions take a different path from first questions.
- Retrieval always returns the 4 closest chunks, however weak the match. There is no minimum similarity score, so an off-topic question still gets 4 chunks of context. (verify)
- The answer prompt is the library's default. I have not written an instruction that limits the answer to the source documents. (verify)
- The source links shown under an answer are the pages of all retrieved chunks, not only the ones the answer actually used. (verify)
- The knowledge base is 3 Wikipedia pages (M-Pesa, Safaricom, Central Bank of Kenya), the National Payment System Act, and the National Payment System Regulations, 2014. Every test question must be answerable, or deliberately unanswerable, from these five sources.

Anything below marked **(verify)** is a hypothesis to confirm when I run the tests.

## 2. How risk is scored

Risk = **Impact** (what a user loses if this goes wrong) × **Likelihood** (how fragile or complex the area is). Each is scored 1 to 5, so scores run from 1 to 25.

- **Impact 5:** a user could act on false information about money, fees or the law, or private data is exposed.
- **Impact 3:** a wrong or unhelpful answer that the user would probably notice.
- **Impact 1:** a cosmetic problem.
- **Likelihood 5:** it would happen often with ordinary use.
- **Likelihood 3:** it happens with some effort or in specific cases.
- **Likelihood 1:** it needs unusual conditions.

## 3. Risk map

| # | Area | What could go wrong | Impact | Likelihood | Score | Approach |
|---|------|---------------------|:------:|:----------:|:-----:|----------|
| R1 | **Hallucination** | The bot states a fee, limit, date or legal requirement that is not in the sources, or contradicts them | 5 | 4 | **20** | Automate against verified ground truth, plus questions whose answer is not in the documents |
| R2 | **Source citation** | The links shown do not support the answer, or links appear on an answer the sources do not cover | 4 | 4 | **16** | Automate (compare returned links to the expected source for each question) |
| R3 | **Out-of-scope questions** | The bot answers general questions (recipes, other countries' rules, other companies) from the model's own knowledge instead of saying it does not know | 4 | 4 | **16** | Automate (off-topic and near-topic questions that must be refused) |
| R4 | **Prompt injection** | A user message such as "ignore your instructions" changes the bot's behaviour or makes it reveal its instructions | 4 | 3 | **12** | Automate (attack set) + exploratory |
| R5 | **Retrieval quality** | The right chunk is not among the 4 retrieved, or a legal section is cut so the answer loses its condition | 4 | 3 | **12** | Automate (check that the expected source section is retrieved) |
| R6 | **Follow-up questions** | A follow-up such as "what about its fees?" is rewritten with the wrong subject, or earlier turns confuse the answer | 3 | 4 | **12** | Automate (multi-turn tests) |
| R7 | **Swahili and mixed-language questions** | A question in Swahili or Sheng gets no match, because the sources are in English, and the bot answers wrongly instead of refusing | 3 | 4 | **12** | Automate (small set) + exploratory |
| R8 | **Data leakage** | The bot reveals its system prompt, configuration or keys, or content that is not from the knowledge base | 5 | 2 | **10** | Automate (attack set) |
| R9 | **Bias and fairness** | Answer quality or tone changes with how the user is described (a farmer, a student, a business, a non-native speaker) or the bot makes unfair claims about a provider | 3 | 3 | **9** | Automate (paired questions) + exploratory |
| R10 | **Model and prompt drift** | A model version, prompt or chunking change silently alters answers that used to be right | 3 | 3 | **9** | Regression suite run in CI as a quality gate |
| R11 | **Cost, latency and abuse** | Very long inputs or repeated calls make the bot slow or expensive, and the endpoint has no rate limiting | 3 | 3 | **9** | Measure response time per test; exploratory (verify) |
| R12 | **Input robustness** | An empty, very long or malformed request (bad history, wrong field types) causes a server error instead of a clear message | 3 | 3 | **9** | Automate (API negative tests) |
| R13 | **Superseded or draft rules** | The bot presents an older rule as current, or a draft as enacted law, for example by mixing the Act with a Wikipedia summary that is out of date | 4 | 2 | **8** | Automate (questions on rules where the sources disagree) |

## 4. Top risks that drive the plan

1. **Hallucination (20):** a confident wrong answer about money or the law is the worst outcome, so most of the ground-truth questions go here.
2. **Source citation (16) and out-of-scope questions (16):** the bot's value is that it answers only from its documents and shows which one. If either fails, a user cannot trust it.
3. **Prompt injection, retrieval quality, follow-ups and Swahili (12 each):** these decide whether the answers stay correct when the input is not a clean first question.

## 5. Out of scope

- Training, fine-tuning or changing the OpenAI model itself
- Security of the OpenAI and Pinecone services
- Load testing at scale (I only measure single-request latency)
- Visual design and accessibility of the chat page
- Whether the legal text is itself correct. I test that the bot reports what its sources say.
- Voice, images and any language other than English and Swahili

I separate real defects from design choices. For example, the chatbot has no user login. That is a choice of the original design, so I note it in the write-up rather than log it as a bug.
