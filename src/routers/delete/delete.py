import logging
from fastapi import APIRouter, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from typing import Annotated
from services.elasticSearch.delete_documents.delete_documents import DeleteDocuments

logger=logging.getLogger(__name__)





delete_router = APIRouter(route_class=DishkaRoute,
                         prefix="/delete",
                         tags=["delete"])



@delete_router.delete("/allDocInIndex")
async def delete_all_doc_index(index_name: str, delete_service: Annotated[DeleteDocuments, FromDishka()] ):
    return await delete_service.delete_all_docuemnts_in_index(index_name)


        

@delete_router.delete("/index")
async def delete_index(index_name: str, delete_service: Annotated[DeleteDocuments, FromDishka()]):
    return await delete_service.delete_index(index_name)

