import { NextResponse } from 'next/server';
import {ask} from "@/utils/chain";
import {Message} from "@/types/message";

// POST /api/chat. Request: {query, history}. Response: {role, content, links, contexts}.
// The evals call this endpoint as a black box, so the response shape must not change.
export async function POST(request: Request) {

    const body = await request.json();
    const question: string = body.query;
    const history: Message[] = body.history ?? []

    /* drop assistant messages before the first user message, keep the roles on the rest */
    // The page starts with an assistant greeting. Sent as history it would make the chain think a
    // conversation had started, and a first "hi" would be rewritten into a made-up question.
    // Everything from the first user message onward is kept, as "Human: ..." and "Assistant: ..."
    // lines, so the rewrite step can tell who said what. With nothing left, the question is left unchanged.
    const firstUser = history.findIndex(h => h.role === "user")
    const keptHistory = firstUser === -1 ? [] : history.slice(firstUser)
    const chatHistory: string = keptHistory
        .map(h => `${h.role === "user" ? "Human" : "Assistant"}: ${h.content}`)
        .join("\n")

    const res = await ask(question, chatHistory)

    console.log(res.sourceDocuments)

    /* no links when the reply did not use the sources (greeting, refusal, "I don't know") */
    // usedSources comes from the model's structured reply. Links are built from the retrieved chunks,
    // so without this check a refusal would still list whatever sources happened to be retrieved.
    const content: string = res.text.trim()

    const links: string[] = !res.usedSources ? [] : Array.from(new Set(res.sourceDocuments.map((document) => document.metadata.source as string)))
    // contexts is always returned: the metrics evals (faithfulness, recall) read it to judge the answer against the chunks.
    const contexts: string[] = res.sourceDocuments.map((document: {pageContent: string}) => document.pageContent)
    return NextResponse.json({role: "assistant", content: content, links: links, contexts: contexts})
}
