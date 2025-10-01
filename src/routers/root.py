from fastapi import APIRouter
import logging
from dishka.integrations.fastapi import DishkaRoute
from fastapi.responses import RedirectResponse
from .query.query import query_router
from .delete.delete import delete_router
from .fetch.fetch import fetch_router
from .query.semantic_query import semantic_query_router
from .query.get_all import get_all_router
from .index_manager.index_manager import index_manager_router
__all__ = ('root_routes',) #scrivere questo serve perche dice cosa esportare qunado si scrive from root import *. In questo caso esporta solo root_routes
logger = logging.getLogger(__name__)

root_routes = APIRouter(route_class=DishkaRoute)






all_routes : tuple [APIRouter,...] = (
                    query_router,
                    delete_router,
                    fetch_router,
                    semantic_query_router,
                    get_all_router,
                    index_manager_router
                )


for rout in all_routes:
    root_routes.include_router(rout)


@root_routes.get("/", tags=["general"])
async def documentation() -> RedirectResponse: #restituisce un oggetto di tipo RedirectResponse con codice 307
    return RedirectResponse(url="/docs")  # Reindirizza alla documentazione interattiva di FastAPI (Swagger UI)




