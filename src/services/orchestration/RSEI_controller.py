import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
from services.registry.registry import RegistryService
from services.scraper.scraper import ScraperService
from .last_check_timestamp import TimestampManager
from services.elasticSearch.update_documents.lineage_update_in_v1 import LineageUpdateV1
from services.stac_catalog.STAC_manager import STACManager
from services.orchestration.RSEI_status import RSEIStatus

import asyncio
from fastapi import HTTPException
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


process_lock = asyncio.Lock()

class RSEIController():
    def __init__(self,
                 es_conn: ElasticSearchConnection,
                 embedder: EmbeddingService, 
                 scraper: ScraperService, 
                 indexer: IndexService, 
                 registry: RegistryService, 
                 timestamp: TimestampManager,
                 STACManager: STACManager,
                 status: RSEIStatus
                 ):
        self.es_con = es_conn
        self.embedder = embedder
        self.scraper = scraper
        self.indexer = indexer
        self.registry = registry
        self.timestamp = timestamp
        self.STACManager = STACManager
        self.status= status
        
    async def SFEI_init(self):

        
        es_total_success = 0
        embed_total_success = 0
        es_total_errors = []
        embed_total_failed = []
        
        try: 
            # Registry
            await self.status.start_process()
            yProvIstanceList = await self.registry.update_active_list()
            logger.debug(f"Found {len(yProvIstanceList)} istances")         
            
            if not yProvIstanceList:
                logger.warning("No yProvStore instances found, process interrupted")
                await self.status.interrupt_process("No yProvStore instances found, process interrupted")
                return
            
            for idx, istance in enumerate(yProvIstanceList, 1):
                await self.status.update_details(f"Processing {idx}/{len(yProvIstanceList)}: {istance}")
                await self.status.update_counters(es_indexed=es_total_success,
                                                es_errors=len(es_total_errors), 
                                                embed_success= embed_total_success, 
                                                embed_errors=len(embed_total_failed))
                last_fetch = self.timestamp.get_last_fetch(istance)
                
                async for documents in self.scraper.fetch_document_stream(istance, last_fetch):
                    # Embedding
                    enriched_batch, embed_failed = await self.embedder.add_embeddings_to_batch(documents)
                    embed_total_success += len(enriched_batch)
                    embed_total_failed.extend(embed_failed)
                    
                    #data extraction
                    

                    # Indexing
                    es_success, es_errors = await self.indexer.index_enriched_batch(enriched_batch)
                    es_total_success += es_success
                    es_total_errors.extend(es_errors)
                    
                    # STAC catalog update
                    await asyncio.to_thread(self.STACManager.catalogListUpdate, enriched_batch)
                    await self.status.update_counters(es_indexed=es_total_success,
                                                        es_errors=len(es_total_errors), 
                                                        embed_success= embed_total_success, 
                                                        embed_errors=len(embed_total_failed))
                
                    
                self.timestamp.update_last_fetch(istance)
            
            await self.status.complete_process(es_indexed=es_total_success,
                                                es_errors=len(es_total_errors), 
                                                embed_success= embed_total_success, 
                                                embed_errors=len(embed_total_failed))

            
        except Exception as e: 
            logger.error(f"SFEI error: {e}", exc_info=True)
            await self.status.error_process(error_message=str(e), 
                                            es_indexed=es_total_success,
                                            es_errors=len(es_total_errors), 
                                            embed_success= embed_total_success, 
                                            embed_errors=len(embed_total_failed))

