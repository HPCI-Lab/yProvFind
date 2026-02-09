from settings import settings
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from .full_text_search import FullTextSearch
from .semantic_search import SemanticSearch
from .all_documents import AllDocuments
from dishka import Provider, provide, Scope





class MultiMatchSearchProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def queryservice(self, es_conn: ElasticSearchConnection) -> FullTextSearch:
        return FullTextSearch(es_conn)
    

class SemanticSearchProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def semantic_search(self, es_conn: ElasticSearchConnection, embedding: EmbeddingService) ->SemanticSearch:
        return SemanticSearch(es_conn, embedding)
    

class AllDocumentsProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def all_documents(self, es_conn: ElasticSearchConnection) -> AllDocuments:
        return AllDocuments(es_conn)