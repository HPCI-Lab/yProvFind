from dishka import Provider, provide, Scope
import logging
from ..fetcher.fetcher import DocumentFetcher
from .indexer import IndexService
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService

logger =logging.getLogger(__name__)



    
class IndexerProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_indexer(
        self,
        es_conn: "ElasticSearchConnection",
        fetcher: "DocumentFetcher",
        embedder: "EmbeddingService"
    ) -> IndexService:
        return IndexService(es_conn, fetcher, embedder)




       