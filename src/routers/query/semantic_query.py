import logging 
from fastapi import APIRouter
from fastapi import  APIRouter, Query, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.query_search.semantic_search import SemanticSearch
from typing import Annotated, List , Dict, Any
logger = logging.getLogger(__name__)


semantic_query_router= APIRouter(route_class= DishkaRoute,
                        prefix="/semantic_searc",
                        tags=["search"])


@semantic_query_router.get("/simple")
async def semantic_search_endpoint(query: str, semantic: Annotated[SemanticSearch, FromDishka()])-> List[Dict[str, Any]]:
    try:
        results = await semantic.semantic_search(query)
        return results

    except Exception as e:
        logger.error(f"Errore durante la ricerca semantica: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Errore durante la ricerca: {str(e)}"
        )
    
@semantic_query_router.get("/hybrid_search")
async def hybrid_search_endpoint(query:str, semantic: Annotated[SemanticSearch, FromDishka()])->List[Dict[str, Any]]:
    try: 
        results= await semantic.hybrid_search_native(query)
        return results

    except Exception as e: 
        logger.error(f"Errore durante la ricerca ibrida: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Errore durante la ricerca ibrida: {str(e)}"
        )
    
