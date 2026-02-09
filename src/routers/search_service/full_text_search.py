import logging
from pydantic import BaseModel
from datetime import date
from typing import Any, Dict, List, Optional
from fastapi import  APIRouter, Query
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.search_service.full_text_search import FullTextSearch
from typing import Annotated 

logger= logging.getLogger(__name__)


query_router = APIRouter(route_class=DishkaRoute,
                         prefix="/search",
                         tags=["Search"])


class FullTextResponse(BaseModel):
    id: str
    score: Optional[float] = None
    source: Dict[str, Any]
    other_versions: Optional[List[Dict[str, Any]]] = None


@query_router.get("/fulltext",     
                    summary="Simple full-text search on the title, description, keywords, author, PID fields",
                    description="Full-text search in Elasticsearch analyzes text by tokenizing and normalizing it, then matches query terms against the tokens. It ranks results using relevance scoring with the BM25 algorithm.",
                    response_description="List of retrived documents ordered by score",
                    response_model=List[FullTextResponse]
                )
async def search(
    full_text_search: Annotated[FullTextSearch, FromDishka()],
    query: str = Query(None, description="es. climate"),
    page_size : Optional[int] = Query(10, description="es. 10"),
    other_versions: bool = False,
    date_from: Optional[date] = Query(None, description="format: yyyy-mm-dd"),
    date_to: Optional[date] = Query(None, description="format: yyyy-mm-dd"),
    version: Optional[int] =  Query(None, description="es. 3"),
    yProvIstance: Optional[str] = Query(None, description="es. http://localhost:8000")

    
) -> List[FullTextResponse]:
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "version": version,
        "yProvIstance": yProvIstance,
    }
    return await full_text_search.search(query, filters, page_size, other_versions)
