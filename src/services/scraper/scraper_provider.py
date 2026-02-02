from dishka import Provider, provide, Scope
import logging
from .scraper import ScraperService
from typing import AsyncIterator



logger =logging.getLogger(__name__)


class ScraperProvider(Provider):
    @provide(scope=Scope.APP)
    async def start_scraper(self) -> AsyncIterator[ScraperService]:
        scraper = ScraperService()
        try:
            yield scraper
        finally:
            await scraper.close()