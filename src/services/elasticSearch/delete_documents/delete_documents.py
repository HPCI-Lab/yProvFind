import logging
from ..connection.es_connection import ElasticSearchConnection
from settings import settings
from elasticsearch import NotFoundError
import elasticsearch.exceptions as ElasticsearchException

logger = logging.getLogger(__name__)



class DeleteDocuments:
    def __init__ (self, es_conn: ElasticSearchConnection):
        self.client= es_conn.client


    async def delete_all_docuemnts_in_index(self, index_name: str):
        logger.debug(f"all the documents in index : {index_name} wil be eliminated but not the index")
        try:
            resp = await self.client.delete_by_query(
                index=index_name,
                body= {"query": {"match_all": {}}}
            )
            logger.info(
                f"Delete by query completed on index '{index_name}': "
                f"total={resp.get('total')}, "
                f"deleted={resp.get('deleted')}, "
                f"failures={resp.get('failures')}"
            )
            return {
                "status": "success",
                "index": index_name,
                "total": resp.get("total"),
                "deleted": resp.get("deleted"),
                "failures": resp.get("failures"),
            }
        except NotFoundError:
            logger.warning(f"Index '{index_name}' not found")
            return {
                "status": "error",
                "message": "Index not found",
                "index": index_name
            }
        except ElasticsearchException as e:
            logger.error(f"Elasticsearch error during deletion in index '{index_name}': {e}")
            return {
                "status": "error", 
                "message": f"Elasticsearch error: {str(e)}",
                "index": index_name
            }
        except Exception as e:
            logger.error(f"Unexpected error during deletion in index '{index_name}': {e}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "index": index_name
            }
        


        
    async def delete_index(self, index_name:str):

        try:
            results = await self.client.indices.delete(index=index_name)
            logger.debug(f"eliminated index: {index_name}")
            return {
                "status": "success",
                "index" : index_name,
                
            }
        
        except NotFoundError:
            logger.error("index not found")
            return {
                "status": "error",
                "index": index_name,
                "message": "index not found"
                
            }

        except Exception as e:
            logger.error("index not eliminated")
            return {
                "status": "error",
                "index": index_name,
                "message": "internal error"
            }
