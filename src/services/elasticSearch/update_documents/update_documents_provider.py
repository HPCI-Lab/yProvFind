from dishka import Provider, provide, Scope
from services.elasticSearch.update_documents.lineage_update_in_v1 import LineageUpdateV1
from services.elasticSearch.connection.es_connection import ElasticSearchConnection

class UpdateDocumentsProvider(Provider): 
    @provide(scope=Scope.REQUEST)
    async def update_lineage_in_v1(self, es_conn: ElasticSearchConnection)-> LineageUpdateV1:
        return LineageUpdateV1(es_conn)