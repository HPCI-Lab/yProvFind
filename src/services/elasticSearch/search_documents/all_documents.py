import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from settings import settings
from utils.error_handlers import safe_es_call
logger = logging.getLogger(__name__)

class AllDocuments:
    def __init__(self, es_conn: ElasticSearchConnection):
        self.es_conn=es_conn


    async def get_all_documents(self, timeout: float = 10, include_all_versions: bool = True):
        async def _perform_search():
            body = {
                "query": {
                    "match_all": {}
                },
                "collapse": {
                    "field": "lineage"
                },
                "sort": [
                    {"version": {"order": "desc"}}
                ],
                "_source": {
                    "excludes": ["semantic_embedding"]
                },
                "size": 100
            }
            
            # Aggiungi inner_hits se vuoi anche le altre versioni
            if include_all_versions:
                body["collapse"]["inner_hits"] = {
                    "name": "all_versions",
                    "size": 10,
                    "sort": [{"version": {"order": "desc"}}],
                    "_source": {
                        "excludes": ["semantic_embedding"]
                    }
                }
            
            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=body
            )
            
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source'],
                    'search_type': 'all_documents'
                }
                
                # Aggiungi le altre versioni se richieste
                if include_all_versions and 'inner_hits' in hit:
                    result['other_versions'] = [
                        {
                            'id': inner_hit['_id'],
                            'source': inner_hit['_source']
                        }
                        for inner_hit in hit['inner_hits']['all_versions']['hits']['hits']
                    ]
                
                results.append(result)
            
            return results
        
        return await safe_es_call(_perform_search(), operation_type="search", timeout=timeout)