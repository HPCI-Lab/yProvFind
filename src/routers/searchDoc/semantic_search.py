import logging 
from fastapi import  APIRouter, Query, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.search_documents.semantic_search import SemanticSearch
from typing import Annotated, List , Dict, Any, Optional
from pydantic import BaseModel
from datetime import date


logger = logging.getLogger(__name__)




semantic_query_router= APIRouter(route_class= DishkaRoute,
                        prefix="/search",
                        tags=["search"])




class SemanticSearchResponse(BaseModel):
    id: str
    score: float
    source: Dict[str, Any]
    other_versions: Optional[List[Dict[str, Any]]] = None




@semantic_query_router.get(
    "/semantic",
    response_model=List[SemanticSearchResponse],
    summary="Ricerca semantica semplice",
    description="Esegue una ricerca semantica su Elasticsearch usando embeddings"
)
async def semantic_search_endpoint( query: str,
                                    semantic: Annotated[SemanticSearch, FromDishka()],
                                    other_versions: bool = False, 
                                    date_from: Optional[date] = None,
                                    date_to: Optional[date] = None,
                                    version: Optional[int] = None,
                                    yProvIstance: Optional[str] = None,
                                    ) -> List[SemanticSearchResponse]:
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "version": version,
        "yProvIstance": yProvIstance,
    }
    return await semantic.semantic_search(query,filters, other_versions )



@semantic_query_router.get("/semanticMultiMatch",
                            response_model=List[SemanticSearchResponse],
                            summary="Ricerca ibrida",
                            description="Esegue una ricerca semantica su Elasticsearch usando embeddings e in parallelo una ricerca multi match full-text con una successiva combinazione dei risultati")
async def hybrid_search_endpoint(query: str,
                                    semantic: Annotated[SemanticSearch, FromDishka()],
                                    other_versions: bool = False, 
                                    date_from: Optional[date] = None,
                                    date_to: Optional[date] = None,
                                    version: Optional[int] = None,
                                    yProvIstance: Optional[str] = None,
                                    ) -> List[SemanticSearchResponse]:
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "version": version,
        "yProvIstance": yProvIstance,
    }
    return await semantic.hybrid_search_native(query, filters, other_versions)




@semantic_query_router.get("/knnMultiMatch",
                            response_model=List[SemanticSearchResponse],
                            summary="Ricerca attraverso il metodo knn",
                            description="integrata la funzinalita di ricerca tramite knn HSNW, un algoritmo che permette di fare la ricerca aproximate Knn ma introduce funzionalita di early stop per dare risultati velocemente e mantenendo comunque una buona precisione")
async def knn_multiMatch_endpoint(query: str,
                                    semantic: Annotated[SemanticSearch, FromDishka()],
                                    other_versions: bool = False, 
                                    date_from: Optional[date] = None,
                                    date_to: Optional[date] = None,
                                    version: Optional[int] = None,
                                    yProvIstance: Optional[str] = None,
                                    ) -> List[SemanticSearchResponse]:
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "version": version,
        "yProvIstance": yProvIstance,
    }
    return await semantic.knn_MultiMatch_search(query, filters, other_versions)