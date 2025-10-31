import logging
from services.embedding.embedder import EmbeddingService
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from typing import Dict, List, Any
from settings import settings
from utils.error_handlers import safe_es_call

logger = logging.getLogger(__name__)


class SemanticSearch():
    def __init__ (self,es_conn: ElasticSearchConnection, embedder: EmbeddingService): 
        self.embedder= embedder
        self.es_conn =es_conn





    async def semantic_search(
        self, 
        query: str, 
        add_filters: Dict,
        include_all_versions: bool = True,
        size: int = 10, 
        min_score: float = 0.01,
        timeout: float = 10.0
    ) -> List[Dict[str, Any]]:
        
        async def _perform_search():
            query_embedding = await self.embedder._get_query_embedding(query)
            
            bool_query = {"must": {"match_all": {}}}

            if add_filters:
                bool_query["filter"] = await self._add_filters(add_filters)

            search_body = {
                "size": size,
                "min_score": min_score,
                "query": {
                    "script_score": {
                        "query": {"bool": bool_query},
                        "script": {
                            "source": "(cosineSimilarity(params.query_vector, 'semantic_embedding') + 1.0) / 2.0",
                            "params": {"query_vector": query_embedding}
                        }
                    }
                },
                "collapse": {
                    "field": "lineage"
                },
                "_source": {
                    "excludes": ["semantic_embedding"]
                }
            }
            
            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=search_body
            )
            
            return await self._add_versions(response, include_all_versions)
        
        return await safe_es_call(_perform_search(), "search", timeout=timeout)











    async def hybrid_search_native(
        self,
        query: str,
        addFilters: Dict,
        include_all_versions: bool,
        size: int = 15,
        text_boost: float = 0.5,
        semantic_boost: float = 2.0,
        timeout: float= 10
        
    ) -> List[Dict[str, Any]]:
        """
        Ricerca ibrida usando le funzionalità native di Elasticsearch 8.0+
        Utilizza il nuovo 'hybrid' retriever
        """
        async def _perform_search():
            query_embedding = await self.embedder._get_query_embedding(query)
            
            # Costruisci le clausole should
            search_clauses = [
                # Clausola 1: Full-text (contribuisce allo score)
                {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["title^3", "description", "keywords^2", "author", "pid"],
                                    "type": "best_fields",
                                    "boost": text_boost   # enfatizza full-text
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["title.ngram^2", "keywords.ngram^1"],
                                    "type": "best_fields",
                                    "boost": text_boost * 2
                                }
                            }
                        ]
                    }
                },
                # Clausola 2: Semantica (contribuisce allo score)
                {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "(cosineSimilarity(params.query_vector, 'semantic_embedding') + 1.0) / 2.0",
                            "params": {"query_vector": query_embedding}
                        },
                        "boost": semantic_boost
                    }
                }
            ]
            
            # Query principale con should
            query_body = {
                "bool": {
                    "should": search_clauses
                    # NESSUN minimum_should_match
                }
            }
            
            # Aggiungi filtri
            if addFilters:
                query_body["bool"]["filter"] = await self._add_filters(addFilters)
            
            search_body = {
                "size": size * 2,
                "query": query_body,
                "collapse": {
                    "field": "lineage"
                },
                "_source": {
                    "excludes": ["semantic_embedding"]
                }
            }
            

            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=search_body
            )
            
            return await self._add_versions(response, include_all_versions)
        

        return await safe_es_call(_perform_search(), "search", timeout=timeout)
        






    async def knn_MultiMatch_search (
        self,
        query: str,
        addFilters: Dict,
        include_all_versions: bool,
        size: int = 10,
        num_results: int = 5,
        num_candidate: int = 10,
        timeout: float = 10.0
            )->List[Dict[str, Any]]: 

        """
            integrata la funzinalita di ricerca tramite knn HSNW, un algoritmo che permette di fare la ricerca aproximate Knn ma introduce
            funzionalita di early stop per dare risultati velocemente e mantenendo comunque una buona precisione
        """

        async def _perform_search():
            query_embedding= await self.embedder._get_query_embedding(query)

            knn_query = {
                "field": "semantic_embedding",
                "query_vector": query_embedding,
                "k": num_results,
                "num_candidates": num_candidate
            }

            # Costruisci la bool query per il filtro testuale
            bool_query = {
                    "should": [  
                        {
                            # Match esatto (alta priorità)
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "description", "keywords^2", "author", "pid"],
                                "type": "best_fields"
                            }
                        },
                        {
                            # Match parziale su ngram (bassa priorità)
                            "multi_match": {
                                "query": query,
                                "fields": ["title.ngram^1", "keywords.ngram^0.5"],
                                "type": "best_fields"
                            }
                        }
                    ],
                    "minimum_should_match": 1  # almeno una clausola deve matchare
                }

            # Aggiungi filtri se presenti
            if addFilters:
                filters = await self._add_filters(addFilters)
                bool_query["filter"] = filters
                knn_query["filter"] = filters  

            search_body = {
                "knn": knn_query,
                "query": {"bool": bool_query},
                "collapse": {
                    "field": "lineage"
                },
                "_source": {
                    "excludes": ["semantic_embedding"]
                }
            }          

            response = await self.es_conn.client.search(
                index= settings.INDEX_NAME,
                body=search_body
            )

            return await self._add_versions(response, include_all_versions)
        
        return await safe_es_call(_perform_search(), "search", timeout=timeout)






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
                # Seconda query recupera TUTTE le versioni per i lineage trovati
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

                        """"
                        # Log per debugging
                        logger.debug(f"Document {hit['_id']} (v{hit['_source'].get('version')}) has {len(result['other_versions'])} other versions")
                        versions_list = [v['source'].get('version') for v in result['other_versions']]
                        logger.debug(f"Other versions: {versions_list}")
                        """
                        
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


