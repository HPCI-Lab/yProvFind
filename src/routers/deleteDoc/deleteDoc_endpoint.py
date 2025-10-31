import logging
from fastapi import APIRouter, Query
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.delete_documents.delete_documents import DeleteDocuments
from typing import Annotated, List , Any, Optional
from pydantic import BaseModel, Field



logger=logging.getLogger(__name__)





delete_router = APIRouter(route_class=DishkaRoute,
                         prefix="/delete",
                         tags=["Delete"])



class DeleteAllDocsResponse(BaseModel):
    status: str = Field(..., description="operation result", example="success")
    index: str = Field(..., description="Index name")
    total: Optional[int] = Field(None, description="Documents number on the index before the elimination")
    deleted: Optional[int] = Field(None, description="Elinated documents")
    failures: Optional[List[Any]] = Field(None, description="Errors during the process")

@delete_router.delete("/all-doc-in-index",
                      summary="Delete all files in an index",
                      description="The endpoint provides a method to delete all indexed files in the designated index without deleting the index itself. This allows you to preserve the existing index mapping.",
                      response_model= DeleteAllDocsResponse
                      )
async def delete_all_doc_index(index_name: Annotated[str, Query(example="documents")], delete_service: Annotated[DeleteDocuments, FromDishka()] )-> DeleteAllDocsResponse:
    return await delete_service.delete_all_docuemnts_in_index(index_name)




