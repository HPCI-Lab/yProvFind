import logging
from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from typing import Annotated
from services.elasticSearch.delete_documents.delete_documents import delete_documents

logger=logging.getLogger(__name__)





delete_router = APIRouter(route_class=DishkaRoute,
                         prefix="/delete",
                         tags=["delete"])

@delete_router.delete("/allDocInIndex")
async def delete_all_doc_index(index_name: str, service: Annotated[delete_documents, FromDishka()] ):
    resp = await service.delete_all_docuemnts_in_index(index_name)
    return resp