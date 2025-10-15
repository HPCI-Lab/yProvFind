
import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from ..scraper.scraper import ScraperService
from elasticsearch.helpers import async_bulk
from services.embedding.embedder import EmbeddingService
from settings import settings
from typing import List, Dict

logger =logging.getLogger(__name__)


class IndexService():
    def __init__(self, es_conn: ElasticSearchConnection, fetcher: ScraperService, embedder: EmbeddingService):
        self.es_conn=es_conn
        self.fetcher=fetcher #il fetcher restituisce un generatore (iteratore)
        self.embedder= embedder

    async def bulk_indexer(self): 
        documents=self.fetcher.fetch_documents_async()

        try: 
            success, errors = await async_bulk(self.es_conn.client, documents)#le bulk di elastich search sono in grado di prendere degli iteratori in modo da poter inserire migliaia di docuemnti senza dover passare liste grandi di dati
            
            
            if errors: 
                for err in errors:
                    logger.error(f"Errore indicizzazione documento {err.get('index', {}).get('_id')}: {err}")
            
            logger.info(f"Indicizzati {success} documenti, {len(errors)} errori")

            return {
                "success_count": success,
                "error_count": len(errors),
                "has_errors": len(errors) > 0
            }
        
        
        except Exception as e: 
            logger.error(f"errors occurs during the fetch of all the files: {e}")
            raise


    async def bulk_indexer_embeddings(self, batch_size : int = settings.BATCH_SIZE):
        total_success=0
        total_errors=[]

        batch=[]

        documents= self.fetcher.fetch_documents_async()
        async for doc in documents:
            batch.append(doc)

            if len(batch)>settings.BATCH_SIZE:
                success, errors = await self._process_and_index_batch(batch)
                total_success += success
                total_errors.extend(errors)

                batch=[]

        if batch: 
            success, errors = await self._process_and_index_batch(batch)
            total_success += success
            total_errors.extend(errors)
        
        return {
            "success_count": total_success,
            "error_count": len(total_errors),
            "has_errors": len(total_errors) > 0
        }



    async def index_enriched_batch(self, enriched_batch: List[Dict]):
        try: 
            success, errors = await async_bulk(self.es_conn.client, enriched_batch)
            return success, errors
        except Exception as e:
            logger.error(f"Errore processing batch: {e}")
            return 0, [{"error": str(e)} for _ in enriched_batch]                     
        


    async def check_current_mapping(self):
        try:
            response = await self.es_conn.client.indices.get_mapping(index= "documents")
            logger.debug(f"mappatura attuale:{response}")
            
            mapping = response["documents"]["mappings"]["properties"]
            if "semantic_embedding" in mapping:
                print(f"Campo semantic_embedding: {mapping['semantic_embedding']}")
            else:
                print("Campo semantic_embedding NON trovato!")
            
        except Exception as e:
            print(f"Errore nel controllo mapping: {e}")