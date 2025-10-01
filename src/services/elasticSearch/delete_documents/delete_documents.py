import logging
from ..connection.es_connection import ElasticSearchConnection
from settings import settings
from elasticsearch import NotFoundError
import elasticsearch.exceptions as ElasticsearchException
from utils.error_handlers import safe_es_call

logger = logging.getLogger(__name__)



class DeleteDocuments:
    def __init__ (self, es_conn: ElasticSearchConnection):
        self.client= es_conn.client


    async def delete_all_docuemnts_in_index(self, index_name: str):
        logger.debug(f"all the documents in index : {index_name} wil be eliminated but not the index")

        async def _delete():
            response = await self.client.delete_by_query(
                index=index_name,
                body= {"query": {"match_all": {}}}
            )
            logger.info(
                f"Delete by query completed on index '{index_name}': "
                f"total={response.get('total')}, "
                f"deleted={response.get('deleted')}, "
                f"failures={response.get('failures')}"
            )
            return {
                "status": "success",
                "index": index_name,
                "total": response.get("total"),
                "deleted": response.get("deleted"),
                "failures": response.get("failures"),
            }
        
        return await safe_es_call(_delete(), "delete")
        


        
    async def delete_index(self, index_name:str):

        async def _delete():
            results = await self.client.indices.delete(index=index_name)
            logger.debug(f"eliminated index: {index_name}")
            return {
                "status": "success",
                "index" : index_name
            }

        return await safe_es_call(_delete(), "delete")


        