from dishka import Scope, provide, Provider
from .scraper import ScraperService


class ScraperProvider(Provider): 
    @provide(scope=Scope.REQUEST)
    async def _ScraperProvider(self)->ScraperService:
        return ScraperService()