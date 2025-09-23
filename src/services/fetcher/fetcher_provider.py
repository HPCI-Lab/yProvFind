from dishka import Provider, provide, Scope
import logging
from .fetcher import DocumentFetcher


logger =logging.getLogger(__name__)


class DocumentFetcherProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def fetch_all(self) -> DocumentFetcher:
        return DocumentFetcher()
    