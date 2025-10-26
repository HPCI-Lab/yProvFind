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
        "number_of_replicas": 1
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
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "description": {
                "type": "text"
            },
            "keywords": {
                "type": "text"
            },
            "author": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
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


@index_manager_router.post("/createIndex")
async def create_index(index_creator: Annotated[CreateIndex, FromDishka()],
                       index_name: Annotated[str, Query(example="documents")],  
                       mapping: Annotated[Dict, Body(example=DOCUMENT_MAPPING_EXAMPLE)]
                       ):
    result = await index_creator.create_index(index_name , mapping)
    return result


class DeleteIndexResponse(BaseModel):
    status: str =Field(..., description="Stato finale dell'operazione", example="success")
    index: str = Field (..., description="Nome dell'indice su cui è stata effettuata l'operazione")    

@index_manager_router.delete("/deleteIndex",
                      summary="Eliminazione totale di un indice",
                      description="permette l'eliminazione di un indice in modo permanente da elasti search, compresa mappatura e file al suo interno",
                      response_model=DeleteIndexResponse
                      )
async def delete_index(index_name:  Annotated[str, Query(example="documents")], delete_service: Annotated[DeleteIndex, FromDishka()])-> DeleteIndexResponse:
    return await delete_service.delete_index(index_name)
