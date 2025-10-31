import logging
from fastapi import APIRouter, HTTPException
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from typing import Annotated
from pydantic import BaseModel
from services.orchestration.last_check_timestamp import TimestampManager



timestamp_router=APIRouter(route_class=DishkaRoute,
                           prefix="/timestamp",
                           tags=["Address timestamp"])


@timestamp_router.get("/all-timestamp", description="retrive all timestamp for every address")
def get_all_timestamp(timeManager: Annotated[TimestampManager, FromDishka()]):
    return timeManager.get_all_last_fetch()


@timestamp_router.delete("/delete-all-timestamp", description="eliminate all the timestamp record for all addresses")
def delete_all_timestamp(timeManager:Annotated[TimestampManager, FromDishka()]):
    return timeManager.delete_all_last_fetch()
    


@timestamp_router.delete("/delete-address-timestamp", description="eliminate the timestamp record for one address")
def delete_address_timestamp(address:str, timeManager: Annotated[TimestampManager, FromDishka()]):
    return timeManager.delete_address_last_fetch(address)






    
