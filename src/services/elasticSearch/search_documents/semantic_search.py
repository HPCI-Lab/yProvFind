import logging
from services.embedding.embedding_service import EmbeddingService
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from typing import Dict, List, Any
import asyncio 
from settings import settings

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
        timeout: float = 30.0
    ) -> List[Dict[str, Any]]:
        """Versione con timeout e retry logic"""
        
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
            
            return [
                {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source'],
                    'similarity': hit['_score'] - 1.0
                }
                for hit in response['hits']['hits']
            ]
        
        try:
            # Esegui con timeout
            results = await asyncio.wait_for(_perform_search(), timeout=timeout)
            logger.info(f"Ricerca completata: {len(results)} risultati per '{query}'")
            return results
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout ({timeout}s) durante la ricerca semantica per '{query}'")
            raise Exception(f"Ricerca timeout dopo {timeout} secondi")
        except Exception as e:
            logger.error(f"Errore ricerca semantica: {str(e)}")
            raise


    async def hybrid_search_native(
        self,
        query: str,
        size: int = 10,
        text_boost: float = 1.0,
        semantic_boost: float = 1.0,
        timeout: float= 30
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
                                "fields": ["title^2", "description", "keywords"]
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

        try:
            results = await asyncio.wait_for(_perform_search(), timeout= timeout)
            logger.info(f"Ricerca completata: {len(results)} risultati per '{query}'")
            return results

        except asyncio.TimeoutError:
            logger.error(f"Timeout ({timeout}s) durante la ricerca semantica per '{query}'")
            raise Exception(f"Ricerca timeout dopo {timeout} secondi")
        except Exception as e:
            logger.error(f"Errore ricerca hybrid search: {str(e)}")
            raise


    