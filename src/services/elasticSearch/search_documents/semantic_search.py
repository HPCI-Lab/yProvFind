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
                },
                "size":size
            }
            
            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=search_body
            )
            
            return await self._add_versions(response, include_all_versions)
        
        return await safe_es_call(_perform_search(), "search", timeout=timeout)



    """

    async def hybrid_search_native(
        self,
        query: str,
        addFilters: Dict,
        include_all_versions: bool,
        size: int = 15,
        text_boost: float = 0.3,
        semantic_boost: float = 1,
        timeout: float = 10
    ) -> List[Dict[str, Any]]:

        async def _perform_search():
            query_embedding = await self.embedder._get_query_embedding(query)

            # Clausole di ricerca (invariato)
            search_clauses = [
                {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["pid.keyword^3"],
                                    "type": "best_fields"
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "title^2", "description", "keywords^1", "author", "pid"
                                    ],
                                    "type": "cross_fields",
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["title.ngram^1", "keywords.ngram^1"],
                                    "type": "best_fields",
                                }
                            }
                        ]
                    }
                },
                {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": 



                                // Score semantico già normalizzato in [0,1]
                                double semantic = (cosineSimilarity(params.query_vector, 'semantic_embedding') + 1.0);

                                // Combinazione pesata
                                double final_score = (semantic * params.semantic_weight);

                                return final_score;
                            ,
                            "params": {
                                "query_vector": query_embedding,
                              
                                "semantic_weight": semantic_boost
                            }
                        },
                        
                    }
                }
            ]

            query_body = {"bool": {"should": search_clauses}}

            if addFilters:
                query_body["bool"]["filter"] = await self._add_filters(addFilters)

            search_body = {
                "size": size,
                "query": query_body,
                "collapse": {"field": "lineage"},
                "_source": {"excludes": ["semantic_embedding"]}
            }

            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=search_body
            )

            return await self._add_versions(response, include_all_versions)

        return await safe_es_call(_perform_search(), "search", timeout=timeout)
    """



 
    async def hybrid_search_native(
        self,
        query: str,
        addFilters: Dict,
        include_all_versions: bool,
        size: int = 15,
        text_boost: float = 0.4,
        semantic_boost: float = 0.6,
        timeout: float = 10
    ) -> List[Dict[str, Any]]:
        
        async def _perform_search():
            query_embedding = await self.embedder._get_query_embedding(query)
            
            # UN'UNICA clausola script_score
            search_clause = {
                "script_score": {
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["pid.keyword^3"],
                                        "type": "best_fields"
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": [
                                            "title^2", "description", "keywords^1", "author", "pid"
                                        ],
                                        "type": "cross_fields",
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["title.ngram^1", "keywords.ngram^1"],
                                        "type": "best_fields",
                                    }
                                }
                            ],
                            "minimum_should_match": 0  # ← IMPORTANTE: permette risultati anche se full-text = 0
                        }
                    },
                    "script": {
                        "source": """
                            // _score contiene lo score full-text (può essere 0 se nessun match)
                            double fulltext = _score;
                            
                            // Normalizzazione dello score full-text
                            double normalized_ft = 0.0;
                            if (fulltext > 0) {
                                double ft_log = Math.log(1.0 + fulltext);
                                normalized_ft = 1.0 / (1.0 + Math.exp(-1.5 * (ft_log - 1.5)));
                            }
                            
                            // Score semantico normalizzato in [0,1]
                            double semantic = (cosineSimilarity(params.query_vector, 'semantic_embedding') + 1.0) / 2.0;
                            
                            // Combinazione pesata
                            double final_score = (normalized_ft * params.text_weight) + 
                                                (semantic * params.semantic_weight);
                            
                            return final_score;
                            """
                        ,
                        "params": {
                            "query_vector": query_embedding,
                            "text_weight": text_boost,
                            "semantic_weight": semantic_boost
                        }
                    }
                }
            }
            
            # Aggiungi i filtri se presenti
            query_body = search_clause
            if addFilters:
                query_body = {
                    "bool": {
                        "must": [search_clause],
                        "filter": await self._add_filters(addFilters)
                    }
                }
            
            search_body = {
                "size": size,
                "query": query_body,
                "collapse": {"field": "lineage"},
                "_source": {"excludes": ["semantic_embedding"]},
                "size":size
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
    size: int = 15,
    text_boost: float = 0.5,
    semantic_boost: float = 0.5,
    timeout: float = 10
    ) -> List[Dict[str, Any]]:
    
        async def _perform_search():
            query_embedding = await self.embedder._get_query_embedding(query)
            
            # Usa kNN per la ricerca semantica come query principale
            search_body = {
                "size": size,
                "knn": {
                    "field": "semantic_embedding",
                    "query_vector": query_embedding,
                    "k": size * 3,  # Prendi più candidati per poi riordinare
                    "num_candidates": 100,
                    "filter": await self._add_filters(addFilters) if addFilters else []
                },
                "query": {
                    "script_score": {
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "multi_match": {
                                            "query": query,
                                            "fields": ["pid.keyword^3"],
                                            "type": "best_fields"
                                        }
                                    },
                                    {
                                        "multi_match": {
                                            "query": query,
                                            "fields": [
                                                "title^2", "description", "keywords^1", "author", "pid"
                                            ],
                                            "type": "cross_fields",
                                        }
                                    },
                                    {
                                        "multi_match": {
                                            "query": query,
                                            "fields": ["title.ngram^1", "keywords.ngram^1"],
                                            "type": "best_fields",
                                        }
                                    }
                                ],
                                "minimum_should_match": 0 
                            }
                        },
                        "script": {
                            "source": """
                                // Score semantico dal kNN (già in _score dal contesto kNN)
                                double semantic = (cosineSimilarity(params.query_vector, 'semantic_embedding') + 1.0) / 2.0;
                                
                                // Score full-text dalla query (può essere 0)
                                double fulltext = _score;
                                
                                // Normalizzazione dello score full-text
                                double normalized_ft = 0.0;
                                if (fulltext > 0) {
                                    double ft_log = Math.log(1.0 + fulltext);
                                    normalized_ft = 1.0 / (1.0 + Math.exp(-1.5 * (ft_log - 1.5)));
                                }
                                
                                // Combinazione pesata
                                double final_score = (semantic * params.semantic_weight) + 
                                                    (normalized_ft * params.text_weight);
                                
                                return final_score;
                            """,
                            "params": {
                                "query_vector": query_embedding,
                                "text_weight": text_boost,
                                "semantic_weight": semantic_boost
                            }
                        }
                    }
                },
                "collapse": {"field": "lineage"},
                "_source": {"excludes": ["semantic_embedding"]},
                "size":size
            }
            
            response = await self.es_conn.client.search(
                index=settings.INDEX_NAME,
                body=search_body
            )
            return await self._add_versions(response, include_all_versions)
        
        return await safe_es_call(_perform_search(), "search", timeout=timeout)




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


