from dishka import Provider, provide, Scope
import logging
from .fetcher import DocumentFetcher
from .indexer import Indexer
from services.elasticSearch.es_connection import ElasticSearchConnection

logger =logging.getLogger(__name__)


class DocumentFetcherProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def fetch_all(self) -> DocumentFetcher:
        return DocumentFetcher()
    

    
class BulkIndexerProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_indexer(
        self,
        es_conn: "ElasticSearchConnection",
        fetcher: "DocumentFetcher"
    ) -> Indexer:
        return Indexer(es_conn, fetcher)




       