import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
from services.scraper.scraper import ScraperService
from services.fetcher.fetcher import DocumentFetcher
from utils.error_handlers import safe_es_call
from dataclasses import dataclass
from typing import List, Dict

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    total_yProv_Istances: int =0,
    processed_istances : int = 0,
    processed_documents : int = 0,
    failed_documents: int = 0,
    errors: List[str] = None
    def __post_init__(self):
        if self.errors is None:
            self.errors = []




class SFEIController (): 
    def __init__ (self, es_conn: ElasticSearchConnection, embedder : EmbeddingService, fetcher: DocumentFetcher, indexer: IndexService, scraper: ScraperService ):
        self.es_con =  es_conn
        self.embedder = embedder
        self.fetcher = fetcher
        self.indexer = indexer
        self.scraper = scraper

        self.stats = ProcessingStats()

    
    async def SFEI_init(self):
        total_success=0
        total_errors=[]

        try: 
            #recupero la lista di istanze yprov dallo scraper
            yProvIstanceList= await self.scraper.getList()
            self.stats.total_yProv_Istances= len(yProvIstanceList)
            logger.debug(f"trovate {len(yProvIstanceList)} istanze")
                        
            if not yProvIstanceList:
                logger.warning("Nessun servizio trovato!")
                return self.stats
            

            for istance in yProvIstanceList:
                async for page in self.fetcher.fetch_document_stream(istance):
                    enriched_batch = await self.embedder.add_embeddings_to_batch(page)
                    success, errors = await self.indexer._index_enriched_batch(enriched_batch)
                    total_success += success
                    total_errors.extend(errors)

            return {
            "success_count": total_success,
            "error_count": len(total_errors),
            "has_errors": len(total_errors) > 0
            }

                    

        except Exception as e: 
            logger.error(f"SFEI erorr: {e}", exc_info=True)









