from dishka import Scope, Provider, provide
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
from services.registry.registry import RegistryService
from services.scraper.scraper import ScraperService
from services.orchestration.SFEI_controller import SFEIController
from services.orchestration.last_check_timestamp import TimestampManager
from services.elasticSearch.update_documents.lineage_update_in_v1 import LineageUpdateV1

class SFEIProvider (Provider): 
    @provide(scope=Scope.REQUEST)
    async def SFEI_Provider(self,
                            es_conn: "ElasticSearchConnection",
                            embedder: "EmbeddingService",
                            fetcher: "ScraperService",
                            indexer: "IndexService",
                            scraper: "RegistryService",
                            timestamp: "TimestampManager",
                            v1_lineage_updater: "LineageUpdateV1"
                            )->SFEIController:
        return SFEIController(es_conn, embedder, fetcher, indexer, scraper, timestamp, v1_lineage_updater)



