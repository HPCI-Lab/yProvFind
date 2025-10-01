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
        size: int = 10, 
        min_score: float = 0.7,
        timeout: float = 10.0,
        include_all_versions: bool = True
    ) -> List[Dict[str, Any]]:
        
        
        async def _perform_search():
            query_embedding = await self.embedder._get_query_embedding(query)
            
            search_body = {
                "size": size,
                "min_score": min_score,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'semantic_embedding') + 1.0",
                            "params": {"query_vector": query_embedding}
                        }
                    }
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
        size: int = 10,
        text_boost: float = 1.0,
        semantic_boost: float = 1.0,
        timeout: float= 10,
        include_all_versions: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Ricerca ibrida usando le funzionalità native di Elasticsearch 8.0+
        Utilizza il nuovo 'hybrid' retriever
        """
        async def _perform_search():
            query_embedding = await self.embedder._get_query_embedding(query)
                
            search_body = {
                "size": size,
                "query": {
                    "script_score": {
                        "query": {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "description", "keywords", "author"]
                            }
                        },
                        "script": {
                            "source": (
                                "cosineSimilarity(params.query_vector, 'semantic_embedding') * params.semantic_boost "
                                "+ _score * params.text_boost"
                            ),
                            "params": {
                                "query_vector": query_embedding,
                                "text_boost": text_boost,
                                "semantic_boost": semantic_boost
                            }
                        }
                    }
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
        






    async def knn_MultiMatch_search (self,
                         query=str,
                         timeout: float = 10.0,
                         num_results: int = 5,
                         num_candidate: int = 6,
                         include_all_versions: bool = True
                         )->List[Dict[str, Any]]: 
        
        """
            integrata la funzinalita di ricerca tramite knn HSNW, un algoritmo che permette di fare la ricerca aproximate Knn ma introduce
            funzionalita di early stop per dare risultati velocemente e mantenendo comunque una buona precisione
        """

        async def _perform_search():
            query_embedding= await self.embedder._get_query_embedding(query)

            search_body={
                "knn": {
                    "field": "semantic_embedding",
                    "query_vector": query_embedding,
                    "k": num_results,
                    "num_candidates": num_candidate
                },
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "description", "keywords", "author"]
                    }
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
        
        # Se dobbiamo includere tutte le versioni, raccogli i lineage trovati
        if include_all_versions:
            lineages = [hit["_source"].get("lineage") for hit in response["hits"]["hits"] if hit["_source"].get("lineage")]
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
                        logger.debug(result['other_versions'])
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
                    "other_versions": None
                }
                results.append(result)
        
        return results            
            


    