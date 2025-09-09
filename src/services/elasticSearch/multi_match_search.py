import logging
from .es_connection import ElasticSearchConnection
from settings import settings

logger = logging.getLogger(__name__)

class Multi_match_search:
    def __init__(self, es_conn: ElasticSearchConnection):
        self.client=es_conn.client

    async def search(self, query: str):
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                        "fields": ["title^3", "description", "keywords"]  # boost su title
                                }
                    },
                    
        }
        resp = await self.client.search(index=settings.INDEX_NAME, query=body, size=10)
        return resp["hits"]["hits"]
        
        