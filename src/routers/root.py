from fastapi import APIRouter
import logging
from dishka.integrations.fastapi import DishkaRoute
from fastapi.responses import RedirectResponse
from .query.query import query_router
from .delete.delete import delete_router

__all__ = ('root_routes',) #scrivere questo serve perche dice cosa esportare qunado si scrive from root import *. In questo caso esporta solo root_routes
logger = logging.getLogger(__name__)

root_routes = APIRouter(route_class=DishkaRoute)



root_routes.include_router(query_router) # /search endpoint per fare le query
root_routes.include_router(delete_router)



@root_routes.get("/", tags=["general"])
async def documentation() -> RedirectResponse: #restituisce un oggetto di tipo RedirectResponse con codice 307
    return RedirectResponse(url="/docs")  # Reindirizza alla documentazione interattiva di FastAPI (Swagger UI)




