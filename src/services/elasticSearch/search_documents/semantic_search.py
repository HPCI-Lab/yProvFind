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
        timeout: float = 10.0
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
                },
                "sort": ["_score"]
            }
            
            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=search_body
            )
            
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source'],
                    'search_type': 'semantic_search'
                }
                results.append(result)
                
            return results
        
        return await safe_es_call(_perform_search(), "search", timeout=timeout)






    async def hybrid_search_native(
        self,
        query: str,
        size: int = 10,
        text_boost: float = 1.0,
        semantic_boost: float = 1.0,
        timeout: float= 10
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
            
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source'],
                    'search_type': 'hybrid_native'
                }
                results.append(result)
                
            return results
        

        return await safe_es_call(_perform_search(), "search", timeout=timeout)
        






    async def knn_MultiMatch_search (self,
                         query=str,
                         timeout: float = 10.0,
                         num_results: int = 5,
                         num_candidate: int = 6
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

            results=[]
            for hit in response['hits']['hits']:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source'],
                    'search_type': 'knn + multi_match'
                }
                results.append(result)
                
            return results
        
        return await safe_es_call(_perform_search(), "search", timeout=timeout)



            
            


    