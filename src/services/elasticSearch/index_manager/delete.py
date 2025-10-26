import logging
from ..connection.es_connection import ElasticSearchConnection
from settings import settings
from elasticsearch import NotFoundError
import elasticsearch.exceptions as ElasticsearchException
from utils.error_handlers import safe_es_call

logger = logging.getLogger(__name__)




class DeleteIndex():
    def __init__(self, es_conn:ElasticSearchConnection):
         self.es_conn=es_conn

    async def delete_index(self, index_name:str):

        async def _delete():
            results = await self.es_conn.client.indices.delete(index=index_name)
            logger.debug(f"eliminated index: {index_name}")
            return {
                "status": "success",
                "index" : index_name
            }

        return await safe_es_call(_delete(), "delete")
