from dishka import Scope, Provider, provide
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
from services.registry.registry import RegistryService
from services.scraper.scraper import ScraperService
from services.orchestration.RSEI_controller import RSEIController
from services.orchestration.last_check_timestamp import TimestampManager
from services.stac_catalog.STAC_manager import STACManager
from services.orchestration.RSEI_status import RSEIStatus
from services.metadata_enricher.meta_enricher import MetaEnricher


class RSEIStatusProvider(Provider):
    @provide(scope=Scope.APP)
    def RSEI_status_provider(self) -> RSEIStatus:  
        return RSEIStatus()  


class RSEIProvider(Provider): 
    @provide(scope=Scope.APP)
    def RSEI_provider(  
        self,
        es_conn: ElasticSearchConnection,
        embedder: EmbeddingService,
        scraper: ScraperService,
        indexer: IndexService,
        registry: RegistryService,
        timestamp: TimestampManager,
        STACManager: STACManager,
        RSEI_status: RSEIStatus,
        enricher: MetaEnricher
        
    ) -> RSEIController:
        return RSEIController(
            es_conn, 
            embedder, 
            scraper, 
            indexer, 
            registry, 
            timestamp,
            STACManager, 
            RSEI_status,
            enricher
        )