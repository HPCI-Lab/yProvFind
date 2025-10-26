from dishka import Scope, provide, Provider
from .registry import RegistryService


class RegisryProvider(Provider): 
    @provide(scope=Scope.APP)
    def _RegistryProvider(self)->RegistryService:
        return RegistryService()