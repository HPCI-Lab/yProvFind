from dishka import Provider, provide, Scope
import logging
from .fetcher import DocumentFetcher
from typing import AsyncIterator
from services.orchestration.last_check_timestamp import TimestampManager
from services.elasticSearch.connection.es_connection import ElasticSearchConnection


logger =logging.getLogger(__name__)


class DocumentFetcherProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def fetch_all(self) -> AsyncIterator[DocumentFetcher]:
        fetcher = DocumentFetcher()
        try:
            yield fetcher
        finally:
            await fetcher.close()