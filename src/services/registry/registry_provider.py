from dishka import Scope, provide, Provider
from .registry import RegistryService


class RegisryProvider(Provider): 
    @provide(scope=Scope.REQUEST)
    async def _ScraperProvider(self)->RegistryService:
        return RegistryService()