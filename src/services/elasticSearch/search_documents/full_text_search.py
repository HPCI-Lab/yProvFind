import logging
from ..connection.es_connection import ElasticSearchConnection
from settings import settings
from utils.error_handlers import safe_es_call
from typing import List, Dict, Optional, Any



logger = logging.getLogger(__name__)





class FullTextSearch:
    def __init__(self, es_conn: ElasticSearchConnection):
        self.es_conn=es_conn

    async def search(self, query: str, addFilters: Dict,  page_size:int=10, include_all_versions: bool = False, timeout: float = 10,):
        must=[]
        filters=[]

        async def _perform_search():
            bool_query = {
                    "should": [  
                        
                        {
                            # Match esatto su pid
                            "multi_match": {
                                "query": query,
                                "fields": ["pid.keyword^5"],
                                "type": "best_fields"
                            }
                        },
                        {
                            # Match esatto (alta priorità)
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "description", "keywords", "author^2", "pid", "llm_description^0.8"],
                                "type": "cross_fields",
                            }
                        },
                        {
                            # Match parziale su ngram (bassa priorità)
                            "multi_match": {
                                "query": query,
                                "fields": ["title.ngram^1", "keywords.ngram^0.8"],
                                "type": "best_fields"
                            }
                        }
                    ],
                    "minimum_should_match": 1  # almeno una clausola deve matchare
                }

            # Aggiungi filtri se presenti
            if addFilters:
                bool_query["filter"] = await self._add_filters(addFilters)


            body = {
                #"explain": True,
                "query": {
                    "bool": bool_query
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
                "size": page_size 
            }        
            
            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=body
            )
            
            # raccogli i lineage trovati
            
               
            return await self._add_versions(response, include_all_versions)
        
        return await safe_es_call(_perform_search(), operation_type="search", timeout=timeout)
    





    async def _add_versions(self, response: Dict[str, Any], include_all_versions: bool) -> List[Dict[str, Any]]:
        results = []
        
        if not response["hits"]["hits"]:
            return results
        
        if include_all_versions:
            # Raccogli SOLO i lineage veri (non standalone)
            lineages = [
                hit["_source"].get("lineage") 
                for hit in response["hits"]["hits"] 
                if hit["_source"].get("lineage") 
                and not hit["_source"].get("lineage").startswith("standalone_")
            ]
            
            versions_by_lineage = {}
            
            # Se ci sono lineage veri, recupera le versioni
            if lineages:
                logger.debug(f"Lineages found: {lineages}")
                
                versions_body = {
                    "query": {"terms": {"lineage": lineages}},
                    "sort": [
                        {"lineage": {"order": "asc"}},
                        {"version": {"order": "desc"}}
                    ],
                    "_source": {"excludes": ["semantic_embedding"]},
                    "size": 1000
                }
                
                versions_response = await self.es_conn.client.search(
                    index=settings.INDEX_NAME,
                    body=versions_body
                )
                
                # Organizza versioni per lineage
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
            
            # Processa TUTTI i documenti nell'ORDINE ORIGINALE (già ordinato per score)
            for hit in response["hits"]["hits"]:
                lineage = hit["_source"].get("lineage")
                
                result = {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "source": hit["_source"]
                }
                
                # Caso 1: Documento standalone
                if not lineage or lineage.startswith("standalone_"):
                    result["other_versions"] = []
                    logger.debug(f"Standalone document {hit['_id']} with score {hit['_score']}")
                
                # Caso 2: Documento con lineage e versioni trovate
                elif lineage in versions_by_lineage:
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
                    
                    logger.debug(f"Document {hit['_id']} (v{hit['_source'].get('version')}) with score {hit['_score']} has {len(result['other_versions'])} other versions")
                    versions_list = [v['source'].get('version') for v in result['other_versions']]
                    logger.debug(f"Other versions: {versions_list}")
                
                # Caso 3: Documento con lineage ma nessuna versione trovata (edge case)
                else:
                    result["other_versions"] = []
                    logger.debug(f"Document {hit['_id']} with lineage but no versions found")
                
                # Aggiungi nell'ordine originale (che è già ordinato per score!)
                results.append(result)
        
        else:
            # Non includere versioni
            for hit in response["hits"]["hits"]:
                result = {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "source": hit["_source"],
                    "other_versions": None
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

            


    