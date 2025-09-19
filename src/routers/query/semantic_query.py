import logging 
from fastapi import APIRouter
from fastapi import  APIRouter, Query, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.search_documents.semantic_search import SemanticSearch
from typing import Annotated, List , Dict, Any
logger = logging.getLogger(__name__)


semantic_query_router= APIRouter(route_class= DishkaRoute,
                        prefix="/semantic_searc",
                        tags=["search"])


@semantic_query_router.get("/simple")
async def semantic_search_endpoint(query: str, semantic: Annotated[SemanticSearch, FromDishka()])-> List[Dict[str, Any]]:
    return await semantic.semantic_search(query)
    

@semantic_query_router.get("/hybrid_search")
async def hybrid_search_endpoint(query:str, semantic: Annotated[SemanticSearch, FromDishka()])->List[Dict[str, Any]]:
    return await semantic.hybrid_search_native(query)


@semantic_query_router.get("/knnMultiMatch")
async def knn_multiMatch_endpoint(query: str, semantic: Annotated[SemanticSearch, FromDishka()])->List[Dict[str, Any]]:
    return await semantic.knn_MultiMatch_search(query)