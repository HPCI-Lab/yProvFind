import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from dishka import Provider, provide, Scope
from settings import settings


logger = logging.getLogger(__name__)

class CreateIndex():
    def __init__(self, es_conn: ElasticSearchConnection):
        self.es_conn = es_conn

    async def create_index(self, index_name: str, mapping: dict): 
        try: 
            if await self.es_conn.client.indices.exists(index = index_name):
                logger.info(f"Index: {index_name} already exists.")
                return {
                    "status": "exists",
                    "index": index_name
                }
            
            response = await self.es_conn.client.indices.create(index=index_name, body=mapping)
            return{
                "status": "created",
                "index": index_name,
                "response": response
            }

            
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")
            return {
                "status": "error",
                "index": index_name,
                "error": str(e)
            }


