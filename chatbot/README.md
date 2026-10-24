# M-Pesa and Kenya Payments Assistant (system under test)

This folder holds a chatbot that I am using as the system under test for my AI/LLM testing portfolio project.

## What it does

It is a question-answering assistant for M-Pesa and Kenya's mobile-money rules. You can ask things like "What is M-Pesa?" or "What do the regulations say about payment service providers?". The bot is meant to answer only from its source documents and to show which source it used. A bank or fintech support agent could use it to check a rule.

## How it works

The app is a retrieval-augmented generation (RAG) chatbot. When someone asks a question, it does not send it straight to the language model. It first
searches a vector database (Pinecone) for the passages from the source documents that are closest in meaning to the question, then asks an OpenAI
chat model to write an answer from those passages, and shows the source pages it used.

### Structure

| Path | What it does |
|---|---|
| app/page.tsx | The whole chat window as one client component: message list, input box, source links, loading state |
| app/layout.tsx | Root layout: font and page title |
| app/api/chat/route.ts | The only backend endpoint, POST /api/chat. A thin controller: read the request, call the chain, shape the response |
| utils/chain.ts | The retrieval pipeline: model, embeddings, vector store and retriever wired into one LangChain chain |
| utils/pinecone-client.ts | Connects to Pinecone using environment variables |
| types/message.ts | The shape of a chat message: role, content, optional links |
| components/LoadingDots.tsx | The animated dots shown while waiting for an answer |
| public/ | Static images |

### Architecture

- A small monolith on the Next.js 13 App Router: the chat page and one API route live in the same project.
- Stateless: the server stores no conversation. The browser keeps the full conversation and sends it with every request.
- LangChain's ConversationalRetrievalQAChain: when there is chat history it rewrites a follow-up into a standalone question, then retrieves the
  closest passages and answers from them. On the first question, with no history, it skips the rewrite.
- The Pinecone client and the chain are created once, the first time /api/chat is called.

### Data flow

```
Offline (the ingestion script, added in this repo as part of the project)
  source documents -> clean -> chunk -> embed (OpenAI text-embedding-3-small) -> store in Pinecone
                      each stored passage has: text, source (its URL)

Online (a question)
  Browser (app/page.tsx)
     | POST /api/chat  { query, history }
     v
  app/api/chat/route.ts
     | joins the chat history into one block of text
     v
  utils/chain.ts
     1. OpenAI call (only when there is chat history): rewrite a follow-up question into a standalone question
     2. OpenAI embeddings: turn that question into a vector
     3. Pinecone: find the closest stored passages
     4. OpenAI call: write the answer from those passages
     v
  route.ts returns { role, content, links }  (links = unique source URLs)
     v
  Browser shows the answer with its source links
```

Step by step:
1. The user presses Enter. The page adds their message to its state and sends { query, history } to /api/chat.
2. route.ts joins the history into one block of text.
3. The first question makes one OpenAI call, one embeddings call and one Pinecone query. Follow-up questions make a second OpenAI call to rewrite
   the question.
4. route.ts reads the source field of each retrieved passage, removes duplicates, and returns them as links together with the answer text.
5. The page adds the answer to the conversation and shows each link, labelled with the last part of its URL.

### Configuration and main libraries

- Environment variables (in a local .env, never committed): OPENAI_API_KEY, PINECONE_API_KEY and PINECONE_INDEX. See .env.example for the full list.
- Main libraries: Next.js, React, TypeScript, Tailwind CSS, LangChain(@langchain/openai, @langchain/pinecone and @langchain/classic), 
  the OpenAI API and the Pinecone SDK.
- The path alias @/ means the folder root, so @/utils/chain is utils/chain.ts.

## Knowledge base

- Wikipedia articles on M-Pesa and Safaricom (CC BY-SA)
- National Payment System Act 2011
- National Payment System Regulations 2014
- CBK Anti-Money Laundering Guidelines for Mobile Payment Services 2013
- CBK Draft National Payment System Policy 2026 (a draft, not law)

Safaricom's own website is not used because it blocks automated access, and I am not working around that. Every source URL, licence and access date is listed in sources.md at the repo root.

## Running it

1. Copy .env.example to .env and fill in OPENAI_API_KEY, PINECONE_API_KEY and PINECONE_INDEX (never commit .env). Create the Pinecone index as serverless, dimension 1536, metric cosine, and use the same embedding model (text-embedding-3-small) as the app.
2. From inside this chatbot/ folder run `npm install`, then `npm run dev`.
3. Open http://localhost:3000.


