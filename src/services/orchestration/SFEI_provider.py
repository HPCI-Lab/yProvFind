from dishka import Scope, Provider, provide
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
from services.scraper.scraper import ScraperService
from services.fetcher.fetcher import DocumentFetcher
from services.orchestration.SFEI_controller import SFEIController
from services.orchestration.last_check_timestamp import TimestampManager

class SFEIProvider (Provider): 
    @provide(scope=Scope.REQUEST)
    async def SFEI_Provider(self,
                            es_conn: "ElasticSearchConnection",
                            embedder: "EmbeddingService",
                            fetcher: "DocumentFetcher",
                            indexer: "IndexService",
                            scraper: "ScraperService",
                            timestamp: "TimestampManager"
                            )->SFEIController:
        return SFEIController(es_conn, embedder, fetcher, indexer, scraper, timestamp)



