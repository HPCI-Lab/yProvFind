import logging
from dishka import Provider, provide, Scope
from ..connection.es_connection import ElasticSearchConnection
from .delete_documents import DeleteDocuments

logger = logging.getLogger(__name__)


class delete_provider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_delete_documents(self, es_conn: ElasticSearchConnection) -> DeleteDocuments:
        return DeleteDocuments(es_conn)