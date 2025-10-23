import logging
from fastapi import APIRouter, HTTPException
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from typing import Annotated
from services.orchestration.SFEI_controller import SFEIController
from pydantic import BaseModel


logger = logging.getLogger(__name__)

fetch_router= APIRouter(route_class=DishkaRoute,
                        prefix="/fetch",
                        tags=["fetch"]
                        )


class FetchResponse(BaseModel):
        ES_successfully_indexed: int
        ES_error_count: int
        embed_success:int
        embed_error: int
        update_v1_lineage:int
        error_v1_lineage:int

@fetch_router.get("/dateFetch", response_model=FetchResponse)
async def fetch_all( SFEI_controller: Annotated[SFEIController, FromDishka()] ):
    try:
        logger.info("fetch di tutti i documenti")
        result = await SFEI_controller.SFEI_init()
        logger.debug("fetch eseguito")
        return {
            "status": "completed", **result
        }

    except Exception as e: 
        logger.error(f"fetch non riuscito: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Errore durante il fetch dei documenti"
        )

