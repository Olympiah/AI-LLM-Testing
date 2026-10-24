import { Pinecone } from '@pinecone-database/pinecone';

if (!process.env.PINECONE_API_KEY) {
    throw new Error('Pinecone api key var missing');
}

function initPinecone() {
    try {
        return new Pinecone({
            apiKey: process.env.PINECONE_API_KEY ?? '',
        });
    } catch (error) {
        console.log('error', error);
        throw new Error('Failed to initialize Pinecone Client');
    }
}

export const pinecone = initPinecone();
