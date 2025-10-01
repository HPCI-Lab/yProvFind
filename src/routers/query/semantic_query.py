import logging 
from fastapi import  APIRouter, Query, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.search_documents.semantic_search import SemanticSearch
from typing import Annotated, List , Dict, Any, Optional
from pydantic import BaseModel



logger = logging.getLogger(__name__)




semantic_query_router= APIRouter(route_class= DishkaRoute,
                        prefix="/semantic_searc",
                        tags=["search"])




class SemanticSearchResponse(BaseModel):
    id: str
    score: float
    source: Dict[str, Any]
    other_versions: Optional[List[Dict[str, Any]]] = None




@semantic_query_router.get(
    "/simple",
    response_model=List[SemanticSearchResponse],
    summary="Ricerca semantica semplice",
    description="Esegue una ricerca semantica su Elasticsearch usando embeddings"
)
async def semantic_search_endpoint( query: str, semantic: Annotated[SemanticSearch, FromDishka()]) -> List[SemanticSearchResponse]:
    return await semantic.semantic_search(query)



@semantic_query_router.get("/hybrid_search",
                            response_model=List[SemanticSearchResponse],
                            summary="Ricerca ibrida",
                            description="Esegue una ricerca semantica su Elasticsearch usando embeddings e in parallelo una ricerca multi match full-text con una successiva combinazione dei risultati")
async def hybrid_search_endpoint(query:str, semantic: Annotated[SemanticSearch, FromDishka()])->List[SemanticSearchResponse]:
    return await semantic.hybrid_search_native(query)




@semantic_query_router.get("/knnMultiMatch",
                            response_model=List[SemanticSearchResponse],
                            summary="Ricerca attraverso il metodo knn",
                            description="Esegue una ricerca semantica utilizzando il metodo knn e poi gli n risultati li passa in una multi_match search, utile quando sono presenti grandi quantita di file, difatti la ricerca tramite knn ha costo O(log(n)) mentre la riceca full-text ha costo O(n)")
async def knn_multiMatch_endpoint(query: str, semantic: Annotated[SemanticSearch, FromDishka()])->List[SemanticSearchResponse]:
    return await semantic.knn_MultiMatch_search(query)