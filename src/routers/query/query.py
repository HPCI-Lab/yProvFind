import logging
from fastapi import  APIRouter, Query
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.multi_match_search import Multi_match_search
from typing import Annotated

logger= logging.getLogger(__name__)


query_router = APIRouter(route_class=DishkaRoute,
                         prefix="/search",
                         tags=["search"])


@query_router.get("", response_model=None)
async def search(query: str, service: Annotated[Multi_match_search, FromDishka()]):
    results = await service.search(query)
    return {"query": query, "results": results}