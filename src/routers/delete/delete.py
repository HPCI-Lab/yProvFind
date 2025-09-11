import logging
from fastapi import APIRouter, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from typing import Annotated
from services.elasticSearch.delete_documents.delete_documents import delete_documents

logger=logging.getLogger(__name__)





delete_router = APIRouter(route_class=DishkaRoute,
                         prefix="/delete",
                         tags=["delete"])

@delete_router.delete("/allDocInIndex")
async def delete_all_doc_index(index_name: str, service: Annotated[delete_documents, FromDishka()] ):
        try:
            result = await service.delete_all_docuemnts_in_index(index_name)
            if result["status"] == "error":
                if "not found" in result["message"].lower():
                    raise HTTPException(status_code=404, detail=result["message"])
                else:  
                    raise HTTPException(status_code=500, detail=result["message"])
                    
                
            
            return result
        except Exception as e:
            logger.error(f"Endpoint error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")