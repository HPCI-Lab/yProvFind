from dishka import Provider, provide, Scope
import logging
from .indexer import IndexService
from services.elasticSearch.connection.es_connection import ElasticSearchConnection


logger =logging.getLogger(__name__)



    
class IndexerProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_indexer(
        self,
        es_conn: "ElasticSearchConnection"
    ) -> IndexService:
        return IndexService(es_conn)




       