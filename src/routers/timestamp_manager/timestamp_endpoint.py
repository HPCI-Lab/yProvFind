import logging
from datetime import datetime
from fastapi import APIRouter
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from typing import Annotated
from pydantic import BaseModel
from services.orchestration.last_check_timestamp import TimestampManager
from pydantic import BaseModel, field_validator





class TimestampUpdate(BaseModel):
    data: str  # stringa in formato ISO
    
    @field_validator('data')
    @classmethod
    def valida_data_iso(cls, v: str) -> str:
        try:
            # Prova a parsare la data ISO
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(
                'Invalid data format. Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS'
            )

    





timestamp_router=APIRouter(route_class=DishkaRoute,
                           prefix="/timestamp",
                           tags=["Address timestamp"])


@timestamp_router.get("/list", description="retrive all timestamp for every address")
def get_all_timestamp(timeManager: Annotated[TimestampManager, FromDishka()]):
    return timeManager.get_all_last_fetch()


@timestamp_router.delete("/delete-all", description="delete all the timestamp record for all addresses")
def delete_all_timestamp(timeManager:Annotated[TimestampManager, FromDishka()]):
    return timeManager.delete_all_last_fetch()
    


@timestamp_router.delete("/delete", description="delete the timestamp record for one address")
def delete_address_timestamp(address:str, timeManager: Annotated[TimestampManager, FromDishka()]):
    return timeManager.delete_address_last_fetch(address)


@timestamp_router.patch("/timestamps", description="Update timestamp for one address")
async def update_one_timestamp(address: str, update: TimestampUpdate, timeManager: Annotated[TimestampManager, FromDishka()]):
        return timeManager.update_timestmap(address, update.data)

