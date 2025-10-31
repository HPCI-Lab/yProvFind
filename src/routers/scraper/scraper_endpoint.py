import logging
from fastapi import APIRouter, HTTPException
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from typing import Annotated
from services.orchestration.SFEI_controller import SFEIController
from pydantic import BaseModel

from fastapi import HTTPException


logger = logging.getLogger(__name__)

scraper_router= APIRouter(route_class=DishkaRoute,
                        prefix="/fetch",
                        tags=["fetch"]
                        )


class ScraperResponse(BaseModel):
        status: str
        details: str
        ES_successfully_indexed: int
        ES_error_count: int
        embed_success:int
        embed_error: int
        #update_v1_lineage:int
        #error_v1_lineage:int

@scraper_router.get("/date-fetch", response_model=ScraperResponse)
async def fetch_all( SFEI_controller: Annotated[SFEIController, FromDishka()] ):
    try:
        logger.info("Start document fetching")
        result = await SFEI_controller.SFEI_init()
        return result



    except Exception as e: 
        logger.error(f"Fetch failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error during the fetch process: {e}"
        )

