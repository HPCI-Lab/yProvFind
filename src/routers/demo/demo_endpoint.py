from services.demo.demo import Demo
from typing import Annotated
from fastapi import APIRouter
from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka


demo_router= APIRouter(route_class=DishkaRoute,
                       prefix="/demo",
                       tags= ["Demo"])


@demo_router.post("/start", description="start the demo and load some example files in order to try yProvFind")
async def stat_demo(demo : Annotated[Demo, FromDishka()]):
    return await demo.start_demo()

@demo_router.delete("/end", description="end the demo and delete the examples files")
async def end_demo(demo : Annotated[Demo, FromDishka()]):
    return await demo.end_demo()