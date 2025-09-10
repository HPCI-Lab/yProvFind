import logging
from ..connection.es_connection import ElasticSearchConnection
from settings import settings


logger = logging.getLogger(__name__)



class delete_documents:
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
                "index": index_name,
                "total": resp.get("total"),
                "deleted": resp.get("deleted"),
                "failures": resp.get("failures"),
            }
        except Exception as e:
            logger.error(f"errors occurred during the elimination of alla documents in the index {index_name}: {e}")
        

