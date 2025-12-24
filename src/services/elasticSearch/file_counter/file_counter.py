from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from typing import Dict
from utils.error_handlers import safe_es_call
from dishka import Provider, Scope, provide

class FileCounter():
    def __init__(self, es_conn: ElasticSearchConnection):
        self.es_conn = es_conn
        

    async def count_by_country(self):
        
        async def _count():
            body={
                "size": 0,  # Non restituire documenti, solo aggregazioni
                "aggs": {
                    "count_per_address": {  # Nome dell'aggregazione (puoi cambiarlo)
                        "terms": {
                            "field": "yProvIstance",  # Il campo su cui raggruppare
                            "size": 10000  # Numero massimo di bucket da restituire
                        }
                    }
                }
            }

            response = await self.es_conn.client.search(index= "documents", body= body)
            final_response= response.get("aggregations")
            return final_response
        
        return await safe_es_call(_count(), operation_type="search")

            
class FileCounterProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def file_counter_provider(self, es_conn:ElasticSearchConnection)->FileCounter:
        return FileCounter(es_conn=es_conn)

