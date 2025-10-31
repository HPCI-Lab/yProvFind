import logging
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from settings import settings
from utils.error_handlers import safe_es_call
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AllDocuments:
    def __init__(self, es_conn: ElasticSearchConnection):
        self.es_conn=es_conn


    async def get_all_documents(self, 
                                addFilters: Dict,
                                include_all_versions: bool,
                                size: int = 10,
                                timeout: float = 10.0):
        async def _perform_search():
            
            bool_query = {"must": {"match_all": {}}}
            
            if addFilters:
                bool_query["filter"] = await self._add_filters(addFilters)
            
            body = {
                "query": {"bool": bool_query},
                "collapse": {
                    "field": "lineage"
                },
                "sort": [
                    {"version": {"order": "desc"}}
                ],
                "_source": {
                    "excludes": ["semantic_embedding"]
                },
                "size": size
            }

            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=body
            )

            return await self._add_versions(response, include_all_versions)
            
        return await safe_es_call(_perform_search(), operation_type="search", timeout=timeout)
    


    async def _add_versions(self, response: Dict[str, Any], include_all_versions: bool) -> List[Dict[str, Any]]:
        results = []
        
        # Se non ci sono hit, ritorna lista vuota
        if not response["hits"]["hits"]:
            return results
        
        if include_all_versions:
            lineages = [
                hit["_source"].get("lineage") 
                for hit in response["hits"]["hits"] 
                if hit["_source"].get("lineage") 
                and not hit["_source"].get("lineage").startswith("standalone_")
            ]
            logger.debug(f"Lineages found: {lineages}")
        
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
                        "source": hit["_source"]
                    }
                    
                    if lineage and lineage in versions_by_lineage:
                        # Filtra escludendo il documento principale
                        all_versions = versions_by_lineage[lineage]
                        result["other_versions"] = [
                            {
                                "id": v["id"],
                                "score": v["score"],
                                "source": v["source"]
                            }
                            for v in all_versions
                            if v["id"] != hit["_id"]
                        ]
                        
                        # Log per debugging
                        logger.debug(f"Document {hit['_id']} (v{hit['_source'].get('version')}) has {len(result['other_versions'])} other versions")
                        versions_list = [v['source'].get('version') for v in result['other_versions']]
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
                    "other_versions": []
                }
                results.append(result)
        
        return results            
          




    async def _add_filters(self, filters:Dict): 
        _filters=[]
        if filters:
            if filters.get("date_from"):   
                    _filters.append({
                        "range": {
                            "created_at": {   
                                "gte": filters["date_from"]
                            }
                        }
                    })

            if filters.get("date_to"):
                _filters.append({
                    "range": {
                        "created_at": {"lte": filters["date_to"]}
                    }
                })

            if filters.get("version"):
                _filters.append({
                    "term": {
                        "version": filters["version"]
                    }
                })

            if filters.get("yProvIstance"):
                _filters.append({
                    "term": {
                        "yProvIstance": filters["yProvIstance"]
                    }
                })
        return _filters


