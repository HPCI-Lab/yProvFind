from embedding_service import EmbeddingService
from elasticsearch import AsyncElasticsearch
import asyncio
from ..fetch_and_index.fetcher import DocumentFetcher
from logging import getLogger
import json

logger = getLogger(__name__)

async def main():


    fetcher=DocumentFetcher
    embedder = EmbeddingService

    batch=[]
    documents=fetcher.fetch_documents_async()
    async for doc in documents:
        batch.append(doc)
        
    enriched_doc= embedder.add_embeddings_to_batch(batch)
    # Stampa ogni elemento come JSON formattato
    for elemento in enriched_doc:
        logger.info(json.dumps(elemento, indent=2))



asyncio.run(main())

