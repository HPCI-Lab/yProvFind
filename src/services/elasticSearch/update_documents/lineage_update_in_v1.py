import logging
from typing import List, Dict
from settings import settings
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from elasticsearch.helpers import async_bulk
logger = logging.getLogger(__name__)

#questo update viene fatto sempre, anche se la lista conteneva sia la versione 1 che la versione 2 con la versione gia contenete la lineage 
#per evitarlo dovrei fare un controllo e capire se il pid della versione 1 è gia nel database ma a quel punto sarebbero altre chiamate
class LineageUpdateV1:
    def __init__(self, es_conn: ElasticSearchConnection):
        self.es_conn = es_conn

    async def update_lineage(self, v1_id_list: Dict):
        
        
        update=[
                    {
            "_op_type": "update",
            "_index": settings.INDEX_NAME,
            "_id": v1_id,
            "doc": {
                "lineage": lineage
            }
        }
            for v1_id, lineage in v1_id_list.items()
        ]

       
        try:
            success, errors = await async_bulk(self.es_conn.client, update)
            if errors:
                for err in errors:
                    logger.error(f"Errore aggiornamento lineage documento {err.get('update', {}).get('_id')}: {err}")

            logger.debug({"updated v1", success})
            return success, errors

        except Exception as e:
            logger.error(f"Errore critico nell'aggiornamento del lineage: {e}")
            raise


        

    
            