from dishka import Scope, provide, Provider
from .registry import RegistryService
from typing import AsyncIterator

class RegisryProvider(Provider): 
    @provide(scope=Scope.APP)
    async def registry_provider(self)->AsyncIterator[RegistryService]:
        registry= RegistryService()
        try:
            yield registry

        finally:
            await registry.close()
        