import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
from services.registry.registry import RegistryService
from services.scraper.scraper import ScraperService
from .last_check_timestamp import TimestampManager
from services.elasticSearch.update_documents.lineage_update_in_v1 import LineageUpdateV1
from services.stac_catalog.STAC_manager import STACManager

import asyncio

logger = logging.getLogger(__name__)







class SFEIController (): 
    def __init__ (self,
                    es_conn: ElasticSearchConnection,
                    embedder : EmbeddingService, 
                    fetcher: ScraperService, 
                    indexer: IndexService, 
                    scraper: RegistryService, 
                    timestamp: TimestampManager,
                    v1_lineage_updater: LineageUpdateV1,
                    STACManager: STACManager
                    
                    ):
        self.es_con =  es_conn
        self.embedder = embedder
        self.fetcher = fetcher
        self.indexer = indexer
        self.scraper = scraper
        self.timestamp = timestamp
        self.v1_lineage_updater = v1_lineage_updater
        self.STACManager= STACManager
        

        #self.stats = ProcessingStats()

    
    async def SFEI_init(self):
        es_total_success=0
        v1_total_updated=0
        embed_total_success=0

        es_total_errors=[]
        v1_total_errors=[]
        embed_total_failed=[]

        try: 


            #registry
            yProvIstanceList= await self.scraper.getList()
            logger.debug(f"found {len(yProvIstanceList)} istances")         
            if not yProvIstanceList:
                logger.warning("No yProvStore instances found, process interrupted")
                return {"No yProvStore instances found, process interrupted"}
            
            
            for istance in yProvIstanceList:
                last_fetch = await self.timestamp.get_last_fetch(istance)
                
                #scraper
                async for documents, v1_list in self.fetcher.fetch_document_stream(istance, last_fetch):
                    
                    #embedding
                    enriched_batch, embed_failed= await self.embedder.add_embeddings_to_batch(documents)
                    embed_total_success+=len(enriched_batch)
                    embed_total_failed.extend(embed_failed)

                    #indexing
                    es_success, es_errors = await self.indexer.index_enriched_batch(enriched_batch)
                    es_total_success += es_success
                    es_total_errors.extend(es_errors)

                    #version 1 lineage update
                    v1_success, v1_errors = await self.v1_lineage_updater.update_lineage(v1_list)
                    v1_total_updated += v1_success
                    v1_total_errors.extend(v1_errors)

                    #STAC catalog update
                    await asyncio.to_thread(self.STACManager.catalogListUpdate, documents)
                    

                    
                await self.timestamp.update_last_fetch(istance)
                    
            return {
                "ES_successfully_indexed": es_total_success,
                "ES_error_count": len(es_total_errors),
                "embed_success": embed_total_success,        # ← Cambiato
                "embed_error": len(embed_total_failed),      # ← Cambiato
                "update_v1_lineage": v1_total_updated,
                "error_v1_lineage": len(v1_total_errors)
            }

                    

        except Exception as e: 
            logger.error(f"SFEI erorr: {e}", exc_info=True)

        










