
from fastapi import APIRouter
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from services.elasticSearch.file_counter.file_counter import FileCounter
from typing import Annotated

counter_router= APIRouter(prefix="/counter", 
                   route_class=DishkaRoute,
                   tags=["File counter"]
                   )


@counter_router.get("/per-country")
async def country_count(counter: Annotated[FileCounter, FromDishka()]):
    response = await counter.count_by_country()
    return response




