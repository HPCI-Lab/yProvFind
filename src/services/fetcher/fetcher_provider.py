from dishka import Provider, provide, Scope
import logging
from .fetcher import DocumentFetcher
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService

logger =logging.getLogger(__name__)


class DocumentFetcherProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def fetch_all(self) -> DocumentFetcher:
        return DocumentFetcher()
    