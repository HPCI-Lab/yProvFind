from dishka import Provider, provide, Scope
import logging
from .scraper import ScraperService
from typing import AsyncIterator
from services.orchestration.last_check_timestamp import TimestampManager
from services.elasticSearch.connection.es_connection import ElasticSearchConnection


logger =logging.getLogger(__name__)


class ScraperProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def fetch_all(self) -> AsyncIterator[ScraperService]:
        fetcher = ScraperService()
        try:
            yield fetcher
        finally:
            await fetcher.close()