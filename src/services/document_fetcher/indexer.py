
import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from .fetcher import DocumentFetcher
from elasticsearch.helpers import async_bulk


logger =logging.getLogger(__name__)


class Indexer:
    def __init__(self, es_conn: ElasticSearchConnection, fetcher: DocumentFetcher):
        self.es_conn=es_conn
        self.fetcher=fetcher #il fetcher restituisce un generatore (iteratore)

    async def bulk_indexer(self): 
        documents=self.fetcher.fetch_documents_async()

        try: 
            success, errors = await async_bulk(self.es_conn.client, documents)#le bulk di elastich search sono in grado di prendere degli iteratori in modo da poter inserire migliaia di docuemnti senza dover passare liste grandi di dati
            
            
            if errors: 
                for err in errors:
                    logger.error(f"Errore indicizzazione documento {err.get('index', {}).get('_id')}: {err}")
            
            logger.info(f"Indicizzati {success} documenti, {len(errors)} errori")
        
        except Exception as e: 
            logger.error(f"errors occurs during the fetch of all the files: {e}")
