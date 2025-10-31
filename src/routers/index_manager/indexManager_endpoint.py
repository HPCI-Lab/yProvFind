from fastapi import APIRouter, Body, Query
from typing import Annotated, Dict
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from services.elasticSearch.index_manager.create import CreateIndex
from services.elasticSearch.index_manager.delete import DeleteIndex
from pydantic import BaseModel, Field

index_manager_router = APIRouter( route_class=DishkaRoute,
                                 prefix = "",
                                 tags=["Index manager"]
                                )


DOCUMENT_MAPPING_EXAMPLE = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "analysis": {
                "tokenizer": {
                    "edge_ngram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 3,
                    "max_gram": 10,
                    "token_chars": ["letter", "digit"]
                    }
                },
                "analyzer": {
                    "edge_ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_tokenizer",
                    "filter": ["lowercase"]
                    }
                }
                }
            },
            "mappings": {
                "properties": {
                "pid": {
                    "type": "text",
                    "fields": {
                    "keyword": {"type": "keyword"}
                    }
                },
                "version": {
                    "type": "integer"
                },
                "owner_email": {
                    "type": "keyword"
                },
                "storage_url": {
                    "type": "keyword"
                },
                "parent_document_pid": {
                    "type": "keyword"
                },
                "lineage": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                    "keyword": {
                        "type": "keyword"
                    },
                    "ngram": {
                        "type": "text",
                        "analyzer": "edge_ngram_analyzer",
                        "search_analyzer": "standard"
                    }
                    }
                },
                "description": {
                    "type": "text"
                },
                "keywords": {
                    "type": "text",
                    "fields": {
                    "ngram": {
                        "type": "text",
                        "analyzer": "edge_ngram_analyzer",
                        "search_analyzer": "standard"
                    }
                    }
                },
                "author": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                    }
                },
                "semantic_embedding": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine",
                    "index_options": {
                    "type": "int8_hnsw",
                    "m": 16,
                    "ef_construction": 100
                    }
                },
                "created_at": {
                    "type": "date"
                },
                "yProvIstance": {
                    "type": "keyword"
                }
                }
            }
            }


@index_manager_router.post("/create-index")
async def create_index(index_creator: Annotated[CreateIndex, FromDishka()],
                       index_name: Annotated[str, Query(example="documents")],  
                       mapping: Annotated[Dict, Body(example=DOCUMENT_MAPPING_EXAMPLE)]
                       ):
    result = await index_creator.create_index(index_name , mapping)
    return result


class DeleteIndexResponse(BaseModel):
    status: str =Field(..., description="Status of the operation", example="success")
    index: str = Field (..., description="Index name")    

@index_manager_router.delete("/delete-index",
                      summary="Complete elimination of the index",
                      description="completely deletes the index passed as a parameter, including the files inside it and its mapping",
                      response_model=DeleteIndexResponse
                      )
async def delete_index(index_name:  Annotated[str, Query(example="documents")], delete_service: Annotated[DeleteIndex, FromDishka()])-> DeleteIndexResponse:
    return await delete_service.delete_index(index_name)
