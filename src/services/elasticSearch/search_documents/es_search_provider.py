from settings import settings
from ..connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from .multi_match_search import Multi_match_search
from .semantic_search import SemanticSearch
from dishka import Provider, provide, Scope




class Multi_match_search_provider(Provider):
    @provide(scope=Scope.REQUEST)
    async def queryservice(self, es_conn: ElasticSearchConnection) -> Multi_match_search:
        return Multi_match_search(es_conn)
    

class Semantic_search_provider(Provider):
    @provide(scope=Scope.REQUEST)
    async def _semantic_search(self, es_conn: ElasticSearchConnection, embedding: EmbeddingService) ->SemanticSearch:
        return SemanticSearch(es_conn, embedding)