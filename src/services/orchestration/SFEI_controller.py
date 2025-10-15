import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
from services.registry.registry import RegistryService
from services.scraper.scraper import ScraperService
from .last_check_timestamp import TimestampManager
from services.elasticSearch.update_documents.lineage_update_in_v1 import LineageUpdateV1


from dataclasses import dataclass
from typing import List, Dict

logger = logging.getLogger(__name__)







class SFEIController (): 
    def __init__ (self,
                    es_conn: ElasticSearchConnection,
                    embedder : EmbeddingService, 
                    fetcher: ScraperService, 
                    indexer: IndexService, 
                    scraper: RegistryService, 
                    timestamp: TimestampManager,
                    v1_lineage_updater: LineageUpdateV1
                    ):
        self.es_con =  es_conn
        self.embedder = embedder
        self.fetcher = fetcher
        self.indexer = indexer
        self.scraper = scraper
        self.timestamp = timestamp
        self.v1_lineage_updater = v1_lineage_updater

        #self.stats = ProcessingStats()

    
    async def SFEI_init(self):
        total_success=0
        v1_total_updated=0
        total_errors=[]

        try: 


            #recupero la lista di istanze yprov dallo scraper
            yProvIstanceList= await self.scraper.getList()
            #self.stats.total_yProv_Istances= len(yProvIstanceList)
            logger.debug(f"trovate {len(yProvIstanceList)} istanze")
                        
            if not yProvIstanceList:
                logger.warning("Nessun servizio trovato!")
                return {"nessuna istanza"}
            
            
            

            for istance in yProvIstanceList:
                last_fetch = await self.timestamp.get_last_fetch(istance)

                async for documents, v1_list in self.fetcher.fetch_document_stream(istance, last_fetch):
                    
                    
                    enriched_batch = await self.embedder.add_embeddings_to_batch(documents)
                    success, errors = await self.indexer.index_enriched_batch(enriched_batch)
                    total_success += success
                    total_errors.extend(errors)
                    
                    v1_success, v1_errors = await self.v1_lineage_updater.update_lineage(v1_list)
                    v1_total_updated += v1_success
                    if v1_errors:
                        logger.error(f"Errori nell'aggiornamento del lineage per v1: {v1_errors}")
                
                await self.timestamp.update_last_fetch(istance)
                    
            return {
            "success_count": total_success,
            "error_count": len(total_errors),
            "has_errors": len(total_errors) > 0,
            "update_v1_lineage": v1_total_updated
            }

                    

        except Exception as e: 
            logger.error(f"SFEI erorr: {e}", exc_info=True)

        










