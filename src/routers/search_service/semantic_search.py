import logging 
from fastapi import  APIRouter, Query, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.search_service.semantic_search import SemanticSearch
from typing import Annotated, List , Dict, Any, Optional
from pydantic import BaseModel
from datetime import date


logger = logging.getLogger(__name__)




semantic_query_router= APIRouter(route_class= DishkaRoute,
                        prefix="/search",
                        tags=["Search"])




class SemanticSearchResponse(BaseModel):
    id: str
    score: float
    source: Dict[str, Any]
    other_versions: Optional[List[Dict[str, Any]]] = None




@semantic_query_router.get(
    "/semantic",
    response_model=List[SemanticSearchResponse],
    summary="Semantic search",
    description="Semantic search in Elasticsearch uses vector embeddings of queries and documents to measure similarity via cosine similarity, allowing retrieval of results based on meaning rather than exact keyword matches. The score is between 0 and 1 (1 max similarity, 0 no similarity)"
)
async def semantic_search_endpoint(semantic: Annotated[SemanticSearch, FromDishka()],
                                    query: str = Query(None, description="es. climate"),
                                    page_size : Optional[int] = Query(10, description="es. 10"),
                                    other_versions: bool = False,
                                    date_from: Optional[date] = Query(None, description="format: yyyy-mm-dd"),
                                    date_to: Optional[date] = Query(None, description="format: yyyy-mm-dd"),
                                    version: Optional[int] =  Query(None, description="es. 3"),
                                    yProvIstance: Optional[str] = Query(None, description="es. http://localhost:8000")
                                    ) -> List[SemanticSearchResponse]:
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "version": version,
        "yProvIstance": yProvIstance,
    }
    return await semantic.semantic_search(query ,filters, other_versions,page_size )



@semantic_query_router.get("/hybrid",
                            response_model=List[SemanticSearchResponse],
                            summary="Combines semantic search with full-text search",
                            description="Hybrid search in Elasticsearch combines full-text matching and semantic vector " \
                            "similarity, retrieving documents that match keywords while also considering their meaning via " \
                            "embeddings, then computes a final relevance score using a custom scoring script.")
async def hybrid_search_endpoint(   semantic: Annotated[SemanticSearch, FromDishka()],
                                    query: str = Query(None, description="es. climate"),
                                    page_size : Optional[int] = Query(10, description="es. 10"),
                                    other_versions: bool = False,
                                    date_from: Optional[date] = Query(None, description="format: yyyy-mm-dd"),
                                    date_to: Optional[date] = Query(None, description="format: yyyy-mm-dd"),
                                    version: Optional[int] =  Query(None, description="es. 3"),
                                    yProvIstance: Optional[str] = Query(None, description="es. http://localhost:8000")
                                    ) -> List[SemanticSearchResponse]:
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "version": version,
        "yProvIstance": yProvIstance,
    }
    return await semantic.hybrid_search_native(query, filters, other_versions, page_size)




@semantic_query_router.get("/knn-fulltext",
                            response_model=List[SemanticSearchResponse],
                            summary="KNN search with HNSW",
                            description="The endpoint uses HNSW approximate nearest neighbor search, traversing a hierarchical vector graph to efficiently find nearest neighbors while reducing unnecessary computations.")
async def knn_multiMatch_endpoint(  semantic: Annotated[SemanticSearch, FromDishka()],
                                    query: str = Query(None, description="es. climate"),
                                    page_size : Optional[int] = Query(10, description="es. 10"),
                                    other_versions: bool = False,
                                    date_from: Optional[date] = Query(None, description="format: yyyy-mm-dd"),
                                    date_to: Optional[date] = Query(None, description="format: yyyy-mm-dd"),
                                    version: Optional[int] =  Query(None, description="es. 3"),
                                    yProvIstance: Optional[str] = Query(None, description="es. http://localhost:8000")
                                    ) -> List[SemanticSearchResponse]:
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "version": version,
        "yProvIstance": yProvIstance,
    }
    return await semantic.knn_MultiMatch_search(query=query, addFilters=filters, include_all_versions= other_versions, size=page_size)