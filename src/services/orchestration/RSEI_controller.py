import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
from services.registry.registry import RegistryService
from services.scraper.scraper import ScraperService
from .last_check_timestamp import TimestampManager
from services.stac_catalog.STAC_manager import STACManager
from services.orchestration.RSEI_status import RSEIStatus
from services.metadata_enricher.meta_enricher import MetaEnricher
import asyncio
from typing import List, Dict
from collections import defaultdict


from settings import settings

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
                 status: RSEIStatus,
                 enricher: MetaEnricher,

                 ):
        self.es_con = es_conn
        self.embedder = embedder
        self.scraper = scraper
        self.indexer = indexer
        self.registry = registry
        self.timestamp = timestamp
        self.STACManager = STACManager
        self.status = status
        self.enricher = enricher

        self.complete_error_list=defaultdict(list)

        self.interrupt_process:bool = False


    def abort(self):
        self.interrupt_process=True      
        logger.warning("The abort function was called")


    async def get_errors_list(self):
        return self.complete_error_list
        


    async def RSEI_init(self, batch_delay:int=0, batch_size:int=settings.BATCH_SIZE, use_enricher:bool=settings.USE_ENRICHER_LLM):
        self.interrupt_process=False
        self.batch_delay=batch_delay
        self.batch_size =batch_size
        self.use_enricher_llm = use_enricher
        
        es_total_success = 0
        embed_total_success = 0
        es_total_errors:List[Dict]  = []
        embed_total_errors: List[Dict] = []
        first_time=True
        
        try: 
            # Registry
            await self.status.start_process()
            yProvIstanceList = await self.registry.update_active_list()
            logger.debug(f"Found {len(yProvIstanceList)} istances")         
            
            if not yProvIstanceList:
                logger.warning("No yProvStore instances found, process interrupted")
                await self.status.interrupt_process("No yProvStore instances found, process interrupted")
                return
            
            #scraper
            #per ogni istanza fa richiesta provenace
            for idx, instance in enumerate(yProvIstanceList, 1):
                await self.status.update_details(f"Processing {idx}/{len(yProvIstanceList)}: {instance}")
                #aggiorna lo status 
                await self.status.update_counters(es_indexed=es_total_success,
                                                es_errors=len(es_total_errors), 
                                                embed_success= embed_total_success, 
                                                embed_errors=len(embed_total_errors),
                                                process_tot_errors=len(self.complete_error_list))
                last_fetch = self.timestamp.get_last_fetch(instance)
                try:
                    #strem di documenti, un batch alla volta per non scaricarli tutti in un unico colpo fino a termine lista in yProvStore
                    async for documents in self.scraper.scraper_document_stream(base_url= instance, last_fetch= last_fetch, page_size= self.batch_size):
                        try:
                            if  self.batch_delay>0 and not first_time:
                                logger.warning(f"Delay active for: {self.batch_delay} seconds")
                                await asyncio.sleep(self.batch_delay)
                            #enricher
                            #usa data extraction e llm enricher solo se use_enricher_llm è true
                            if self.use_enricher_llm:
                                documents, errors = await self.enricher.meta_enricher(documents)
                                for err in errors:
                                    self.complete_error_list[err.get("doc")].append(err.get('error'))

                               

                            # Embedding
                            enriched_batch, embed_failed = await self.embedder.add_embeddings_to_batch(documents)
                            embed_total_success += len(enriched_batch)
                            embed_total_errors.extend(embed_failed)
                            for err in embed_failed:
                                self.complete_error_list[err.get("doc")].append(err.get("error"))


                            # Indexing
                            es_success, es_errors = await self.indexer.index_enriched_batch(enriched_batch)
                            es_total_success += es_success
                            es_total_errors.extend(es_errors)
                            for err in es_errors:
                                self.complete_error_list[err.get("doc")].append(err.get("error"))

                            

                            
                            # STAC catalog update
                            await asyncio.to_thread(self.STACManager.catalogListUpdate, enriched_batch)
                            
                            first_time=False

                            #update the status after every batch 
                            await self.status.update_counters(es_indexed=es_total_success,
                                                            es_errors=len(es_total_errors), 
                                                            embed_success= embed_total_success, 
                                                            embed_errors=len(embed_total_errors),
                                                            process_tot_errors=len(self.complete_error_list))
                        except Exception as e:
                            logger.error(f"Orchestrator: One entire batch failed the indicization: {e}")
                            for doc in documents:
                                self.complete_error_list[doc.get("_id")].append(f"error: {e}")

                        #controll if the user has stopped the process
                        if self.interrupt_process:
                            await self.status.interrupt_process("Process terminated by the user")
                            return
                    
                        
                    self.timestamp.update_last_fetch(instance)

                except Exception as e:
                    logger.error(f"Instance: {instance} was skipped due to an error, the timestamp for this address has not been updated ")
                    self.complete_error_list[str(instance)].append({f"All documents from the instance: {instance}"
                    "could not be processed due to an error caused by the yProvStore instance, which may no longer be connected"
                    "to the network. The timestamp was not updated for this address. To try again, restart the indexing process."})
            
            await self.status.complete_process(es_indexed=es_total_success,
                                                es_errors=len(es_total_errors), 
                                                embed_success= embed_total_success, 
                                                embed_errors=len(embed_total_errors),
                                                process_tot_errrors=len(self.complete_error_list))

            
        except Exception as e: 
            logger.error(f"RSEI Orchestrator failed: {e}", exc_info=True)
            await self.status.error_process(error_message=f"Orchestrator: The indexing process failed: {str(e)}", 
                                            es_indexed=es_total_success,
                                            es_errors=len(es_total_errors), 
                                            embed_success= embed_total_success, 
                                            embed_errors=len(embed_total_errors),
                                            process_tot_errors=len(self.complete_error_list))


