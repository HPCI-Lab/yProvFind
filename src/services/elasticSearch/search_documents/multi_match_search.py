import logging
from ..connection.es_connection import ElasticSearchConnection
from settings import settings
from utils.error_handlers import safe_es_call

logger = logging.getLogger(__name__)

class Multi_match_search:
    def __init__(self, es_conn: ElasticSearchConnection):
        self.client=es_conn.client

    async def search(self, query: str, timeout: float=30):
        async def _perform_search():
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "description", "keywords"]  # boost su title
                                    }
                        },
                        
            }

            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=search_body
            )
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source'],
                    'search_type': 'semantic_search'
                }
                results.append(result)
                
            return results
        
        return await safe_es_call(_perform_search(), operation_type="search", timeout=timeout)
        