from typing import Annotated
from fastapi import APIRouter
from dishka.integrations.fastapi import DishkaRoute
from services.elasticSearch.search_documents.all_documents import AllDocuments
from dishka.integrations.fastapi import FromDishka
from typing import Optional
from datetime import date



get_all_router= APIRouter(route_class=DishkaRoute,
                          prefix="/search",
                          tags=["Search"],
                          )

@get_all_router.get("/all",
                    summary = " get all docuements of the index documents")
async def get_all_documents(all: Annotated[AllDocuments, FromDishka()],
                                    other_versions: bool = False, 
                                    date_from: Optional[date] = None,
                                    date_to: Optional[date] = None,
                                    version: Optional[int] = None,
                                    yProvIstance: Optional[str] = None,):
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "version": version,
        "yProvIstance": yProvIstance,
    }
    return await all.get_all_documents(filters, other_versions)
