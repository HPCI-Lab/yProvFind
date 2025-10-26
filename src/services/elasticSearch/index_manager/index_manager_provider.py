import logging
from dishka import Provider, provide, Scope
from ..connection.es_connection import ElasticSearchConnection
from .delete import DeleteIndex
from .create import CreateIndex

logger = logging.getLogger(__name__)


class IndexManagerProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_create_index(self, es_conn: ElasticSearchConnection)-> CreateIndex:
        return CreateIndex(es_conn)

    @provide(scope=Scope.REQUEST)
    async def delete_index(self, es_conn: ElasticSearchConnection)-> DeleteIndex:
        return DeleteIndex(es_conn)
