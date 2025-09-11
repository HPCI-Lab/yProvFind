import logging

from fastapi import  APIRouter, Query, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.query_search.multi_match_search import Multi_match_search
from typing import Annotated #annotated è linguaggio standard python e serve per aggiungere metadata ai type hints
                            # va usato qunado potrebbe andare in conflitto con fastapi, come in questo caso degli endpoint
                            #invece qunando creiamo classi con l'injection non serve perche __init__ è gestito da dishka

logger= logging.getLogger(__name__)



query_router = APIRouter(route_class=DishkaRoute,
                         prefix="/search",
                         tags=["search"])


#usiamo Annotated 

#qua usiamo Annotated perche aggiungiamo al type hint "Multi_match_search" il metadata "FromDishka"
#questo ci serve perche cosi qunado fast aspi va a vedere il tipe hint e legge dai metadati FromDishka lascia gestire la dipendenza a dishka invece che usare le sue
@query_router.get("", response_model=None)
async def search(query: str, service: Annotated[Multi_match_search, FromDishka()]):
    try:
        results = await service.search(query)
        return {"query": query, "results": results}
    except Exception:
        raise HTTPException(status_code=500, detail="Search service unavailable")
