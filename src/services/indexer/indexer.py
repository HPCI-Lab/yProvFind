
import logging
from settings import settings
from typing import List, Dict

from elasticsearch.helpers import async_bulk

from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.scraper.scraper import ScraperService
from services.embedding.embedder import EmbeddingService



logger =logging.getLogger(__name__)


class IndexService():
    def __init__(self, es_conn: ElasticSearchConnection, fetcher: ScraperService, embedder: EmbeddingService):
        self.es_conn=es_conn
        self.fetcher=fetcher #il fetcher restituisce un generatore (iteratore)
        self.embedder= embedder


    async def index_enriched_batch(self, enriched_batch: List[Dict]):

        try: 
            success, errors = await async_bulk(
            self.es_conn.client, 
            enriched_batch,
            raise_on_error=False,  # Non solleva eccezione se alcuni docs falliscono
            raise_on_exception=False  # Continua anche con errori di connessione
        )
            return success, errors
        except Exception as e:
            logger.error(f"Indexer: failed to index with async_bulk: {e}")
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