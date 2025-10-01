import logging
from ..connection.es_connection import ElasticSearchConnection
from settings import settings
from utils.error_handlers import safe_es_call



logger = logging.getLogger(__name__)





class Multi_match_search:
    def __init__(self, es_conn: ElasticSearchConnection):
        self.es_conn=es_conn

    async def search(self, query: str, timeout: float = 10, include_all_versions: bool = True):
        async def _perform_search():
            # Prima query: trova i documenti più rilevanti
            body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "description", "keywords", "author"]
                    }
                },
                "collapse": {
                    "field": "lineage"
                },
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"version": {"order": "desc"}}
                ],
                "_source": {
                    "excludes": ["semantic_embedding"]
                },
                "size": 10
            }
            
            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=body
            )
            
            results = []
            
            # Se dobbiamo includere tutte le versioni, raccogli i lineage trovati
            if include_all_versions and response["hits"]["hits"]:
                lineages = [hit["_source"].get("lineage") for hit in response["hits"]["hits"] if hit["_source"].get("lineage")]
                
                if lineages:
                    # Seconda query: recupera TUTTE le versioni per i lineage trovati
                    versions_body = {
                        "query": {
                            "terms": {
                                "lineage": lineages
                            }
                        },
                        "sort": [
                            {"lineage": {"order": "asc"}},
                            {"version": {"order": "desc"}}
                        ],
                        "_source": {
                            "excludes": ["semantic_embedding"]
                        },
                        "size": 1000  # Assicurati di prendere tutte le versioni
                    }
                    
                    versions_response = await self.es_conn.client.search(
                        index=settings.INDEX_NAME,
                        body=versions_body
                    )
                    
                    # Organizza le versioni per lineage
                    versions_by_lineage = {}
                    for hit in versions_response["hits"]["hits"]:
                        lineage = hit["_source"].get("lineage")
                        if lineage:
                            if lineage not in versions_by_lineage:
                                versions_by_lineage[lineage] = []
                            versions_by_lineage[lineage].append({
                                "id": hit["_id"],
                                "score": hit.get("_score"),
                                "source": hit["_source"],
                                "version": hit["_source"].get("version")
                            })
                    
                    # Costruisci i risultati con tutte le versioni
                    for hit in response["hits"]["hits"]:
                        lineage = hit["_source"].get("lineage")
                        
                        result = {
                            "id": hit["_id"],
                            "score": hit["_score"],
                            "source": hit["_source"],
                            "search_type": "full_text",
                        }
                        
                        if lineage and lineage in versions_by_lineage:
                            # Filtra escludendo il documento principale
                            all_versions = versions_by_lineage[lineage]
                            result["other_versions"] = [
                                v for v in all_versions
                                if v["id"] != hit["_id"]
                            ]
                            
                            # Log per debugging
                            logger.debug(f"Document {hit['_id']} (v{hit['_source'].get('version')}) has {len(result['other_versions'])} other versions")
                            versions_list = [v.get('version') for v in result['other_versions']]
                            logger.debug(f"Other versions: {versions_list}")
                        else:
                            result["other_versions"] = []
                        
                        results.append(result)
            else:
                # Se non includiamo tutte le versioni, ritorna solo i risultati principali
                for hit in response["hits"]["hits"]:
                    result = {
                        "id": hit["_id"],
                        "score": hit["_score"],
                        "source": hit["_source"],
                        "search_type": "full_text",
                        "other_versions": None
                    }
                    results.append(result)
            
            return results
        
        return await safe_es_call(_perform_search(), operation_type="search", timeout=timeout)