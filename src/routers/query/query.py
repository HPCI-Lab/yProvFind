import logging
from pydantic import BaseModel
from typing import Any, Dict, List
from fastapi import  APIRouter, Query, HTTPException
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.search_documents.multi_match_search import Multi_match_search
from typing import Annotated #annotated è linguaggio standard python e serve per aggiungere metadata ai type hints
                            # va usato qunado potrebbe andare in conflitto con fastapi, come in questo caso degli endpoint
                            #invece qunando creiamo classi con l'injection non serve perche __init__ è gestito da dishka


logger= logging.getLogger(__name__)


query_router = APIRouter(route_class=DishkaRoute,
                         prefix="/search",
                         tags=["search"])


class MultiMatchResponse(BaseModel):
    id: str
    score: float
    source: Dict[str, Any]
    search_type: str


#qua usiamo Annotated perche aggiungiamo al type hint "Multi_match_search" il metadata "FromDishka"
#questo ci serve perche cosi qunado fast aspi va a vedere il tipe hint e legge dai metadati FromDishka lascia gestire la dipendenza a dishka invece che usare le sue
@query_router.get("",     
                    summary="Ricerca full-text semplice",
                    description="Ricerca semplice basata su algoritmo BM25 con tokenizzazione e indice invertito",
                    response_description="Lista di documenti trovati ordinati per score",
                    response_model=MultiMatchResponse
                )
async def search(query: str, multi_match_search: Annotated[Multi_match_search, FromDishka()])->List[MultiMatchResponse]:
    return await multi_match_search.search(query)
