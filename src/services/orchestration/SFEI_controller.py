import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
from services.scraper.scraper import ScraperService
from services.fetcher.fetcher import DocumentFetcher

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
                    logger.debug("metadati ricevuti")
                

                


        except Exception as e: 
            logger.error(f"errore {e}", exc_info=True)









