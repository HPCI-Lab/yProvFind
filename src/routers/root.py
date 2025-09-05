from fastapi import APIRouter
from loggin.logging_config import get_logger
from dishka.integrations.fastapi import DishkaRoute




logger = get_logger(__name__)


root_routes = APIRouter(route_class=DishkaRoute)


@root_routes.get("/", tags=["general"])
async def read_root():
    return {"message": "Welcome to Dishka API!"}