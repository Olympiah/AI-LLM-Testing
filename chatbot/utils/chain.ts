import {ChatOpenAI, OpenAIEmbeddings} from "@langchain/openai";
import {pinecone} from "@/utils/pinecone-client";
import {PineconeStore} from "@langchain/pinecone";
import {ConversationalRetrievalQAChain} from "@langchain/classic/chains";

async function initChain() {
    const model = new ChatOpenAI({
        model: "gpt-4o-mini",
        temperature: 0,
    });

    const pineconeIndex = pinecone.Index(process.env.PINECONE_INDEX ?? '');

    /* create vectorstore*/
    const vectorStore = await PineconeStore.fromExistingIndex(
        new OpenAIEmbeddings({model: "text-embedding-3-small"}),
        {
            pineconeIndex: pineconeIndex,
            textKey: 'text',
        },
    );

    return ConversationalRetrievalQAChain.fromLLM(
        model,
        vectorStore.asRetriever(),
        {returnSourceDocuments: true}
    );
}

export const chain = await initChain()
