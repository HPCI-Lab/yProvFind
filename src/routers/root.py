from fastapi import APIRouter
import logging
from dishka.integrations.fastapi import DishkaRoute
from fastapi.responses import RedirectResponse
from .searchDoc.full_text_search import query_router
from .deleteDoc.deleteDoc_endpoint import delete_router
from .scraper.scraper_endpoint import scraper_router
from .searchDoc.semantic_search import semantic_query_router
from .searchDoc.all_search import get_all_router
from .index_manager.indexManager_endpoint import index_manager_router
from .registry.registry_endpoint import registry_router
from .timestamp_manager.timestamp_manager import timestamp_router
__all__ = ('root_routes',) #scrivere questo serve perche dice cosa esportare qunado si scrive from root import *. In questo caso esporta solo root_routes
logger = logging.getLogger(__name__)

root_routes = APIRouter(route_class=DishkaRoute)






all_routes : tuple [APIRouter,...] = (
                    query_router,
                    delete_router,
                    scraper_router,
                    semantic_query_router,
                    get_all_router,
                    index_manager_router,
                    registry_router,
                    timestamp_router
                )


for rout in all_routes:
    root_routes.include_router(rout)


@root_routes.get("/", tags=["general"])
async def documentation() -> RedirectResponse: #restituisce un oggetto di tipo RedirectResponse con codice 307
    return RedirectResponse(url="/docs")  # Reindirizza alla documentazione interattiva di FastAPI (Swagger UI)




