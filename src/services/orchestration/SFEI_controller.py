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
from fastapi import HTTPException
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


SFEI_status = {
    "status": "idle",  # idle, running, completed, error
    "details": "",
    "ES_successfully_indexed": 0,
    "ES_error_count": 0,
    "embed_success": 0,
    "embed_error": 0,
    "started_at": None,
    "completed_at": None
}


process_lock = asyncio.Lock()

class SFEIController():
    def __init__(self,
                 es_conn: ElasticSearchConnection,
                 embedder: EmbeddingService, 
                 scraper: ScraperService, 
                 indexer: IndexService, 
                 registry: RegistryService, 
                 timestamp: TimestampManager,
                 STACManager: STACManager
                 ):
        self.es_con = es_conn
        self.embedder = embedder
        self.scraper = scraper
        self.indexer = indexer
        self.registry = registry
        self.timestamp = timestamp
        self.STACManager = STACManager
        
    async def SFEI_init(self):
        global SFEI_status
        
        SFEI_status = {
            "status": "running",
            "details": "Initialization...",
            "ES_successfully_indexed": 0,
            "ES_error_count": 0,
            "embed_success": 0,
            "embed_error": 0,
            "started_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        es_total_success = 0
        embed_total_success = 0
        es_total_errors = []
        embed_total_failed = []
        
        try: 
            # Registry
            SFEI_status["details"] = "Retrieving yProvStore instances..."
            yProvIstanceList = await self.registry.update_active_list()
            logger.debug(f"Found {len(yProvIstanceList)} istances")         
            
            if not yProvIstanceList:
                logger.warning("No yProvStore instances found, process interrupted")
                SFEI_status = {
                    "status": "interrupted",
                    "details": "No yProvStore instances found, process interrupted",
                    "ES_successfully_indexed": 0,
                    "ES_error_count": 0,
                    "embed_success": 0,       
                    "embed_error": 0,
                    "started_at": SFEI_status["started_at"],
                    "completed_at": datetime.now().isoformat()
                }
                return
            
            for idx, istance in enumerate(yProvIstanceList, 1):
                SFEI_status["details"] = f"Processing {idx}/{len(yProvIstanceList)}: {istance}"
                last_fetch = self.timestamp.get_last_fetch(istance)
                
                async for documents in self.scraper.fetch_document_stream(istance, last_fetch):
                    # Embedding
                    enriched_batch, embed_failed = await self.embedder.add_embeddings_to_batch(documents)
                    embed_total_success += len(enriched_batch)
                    embed_total_failed.extend(embed_failed)
                    
                    # Indexing
                    es_success, es_errors = await self.indexer.index_enriched_batch(enriched_batch)
                    es_total_success += es_success
                    es_total_errors.extend(es_errors)
                    
                    # STAC catalog update
                    #await asyncio.to_thread(self.STACManager.catalogListUpdate, documents)
                    
                    # Aggiorna lo stato in tempo reale
                    SFEI_status["ES_successfully_indexed"] = es_total_success
                    SFEI_status["ES_error_count"] = len(es_total_errors)
                    SFEI_status["embed_success"] = embed_total_success
                    SFEI_status["embed_error"] = len(embed_total_failed)
                
                self.timestamp.update_last_fetch(istance)
            
            SFEI_status = {
                "status": "completed",
                "details": "Process completed successfully",
                "ES_successfully_indexed": es_total_success,
                "ES_error_count": len(es_total_errors),
                "embed_success": embed_total_success,       
                "embed_error": len(embed_total_failed),
                "started_at": SFEI_status["started_at"],
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e: 
            logger.error(f"SFEI error: {e}", exc_info=True)
            SFEI_status = {
                "status": "error",
                "details": str(e),
                "ES_successfully_indexed": es_total_success,
                "ES_error_count": len(es_total_errors),
                "embed_success": embed_total_success,       
                "embed_error": len(embed_total_failed),
                "started_at": SFEI_status["started_at"],
                "completed_at": datetime.now().isoformat()
            }