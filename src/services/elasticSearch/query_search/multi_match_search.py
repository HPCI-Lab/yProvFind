import logging
from ..connection.es_connection import ElasticSearchConnection
from settings import settings

logger = logging.getLogger(__name__)

class Multi_match_search:
    def __init__(self, es_conn: ElasticSearchConnection):
        self.client=es_conn.client

    async def search(self, query: str):
        try:
            body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "description", "keywords"]  # boost su title
                                    }
                        },
                        
            }
            resp = await self.client.search(index=settings.INDEX_NAME, body=body, size=10)
            return resp["hits"]["hits"]
        
        except Exception as e:
            logger.error(f"error occour during the multi_match search: {e}")
        
        