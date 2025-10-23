from dishka import Provider, provide, Scope
import logging
from .STAC_manager import STACManager



class STACProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def STAC_provider(self)->STACManager:
        return STACManager()
