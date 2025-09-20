import logging
from fastapi import APIRouter, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.delete_documents.delete_documents import DeleteDocuments
from typing import Annotated, List , Any, Optional
from pydantic import BaseModel, Field


logger=logging.getLogger(__name__)





delete_router = APIRouter(route_class=DishkaRoute,
                         prefix="/delete",
                         tags=["delete"])



class DeleteAllDocsResponse(BaseModel):
    status: str = Field(..., description="Stato finale dell'operazione", example="success")
    index: str = Field(..., description="Nome dell'indice su cui è stata effettuata l'operazione")
    total: Optional[int] = Field(None, description="Numero totale di documenti nell'indice prima della cancellazione")
    deleted: Optional[int] = Field(None, description="Numero di documenti effettivamente eliminati")
    failures: Optional[List[Any]] = Field(None, description="Eventuali errori riscontrati durante la cancellazione")

@delete_router.delete("/allDocInIndex",
                      summary="eliminazione tutti file di un indice",
                      description="L'endpoint offre un metodo per eliminare tutti i file indicizzati nell'indice designato senza eliminare l'indice stesso. Permette di mantenere quindi la mappatura dell'indice esistete",
                      response_model= List[DeleteAllDocsResponse]
                      )
async def delete_all_doc_index(index_name: str, delete_service: Annotated[DeleteDocuments, FromDishka()] )-> List[DeleteAllDocsResponse]:
    return await delete_service.delete_all_docuemnts_in_index(index_name)



class DeleteIndex(BaseModel):
    status: str =Field(..., description="Stato finale dell'operazione", example="success")
    index: str = Field (..., description="Nome dell'indice su cui è stata effettuata l'operazione")    

@delete_router.delete("/index",
                      summary="Eliminazione totale di un indice",
                      description="permette l'eliminazione di un indice in modo permanente da elasti search, compresa mappatura e file al suo interno",
                      response_model=List[DeleteIndex]
                      )
async def delete_index(index_name: str, delete_service: Annotated[DeleteDocuments, FromDishka()])-> List[DeleteIndex]:
    return await delete_service.delete_index(index_name)

