import logging
from settings import settings
from ..connection.es_connection import ElasticSearchConnection
from .multi_match_search import Multi_match_search
from dishka import Provider, provide, Scope
from typing import AsyncGenerator



class Multi_match_search_provider(Provider):
    @provide(scope=Scope.REQUEST)
    async def queryservice(self, es_conn: ElasticSearchConnection) -> Multi_match_search:
        return Multi_match_search(es_conn)