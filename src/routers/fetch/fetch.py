import logging
from fastapi import APIRouter, HTTPException
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from typing import Annotated
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.document_fetcher.indexer import Indexer


logger = logging.getLogger(__name__)

fetch_router= APIRouter(route_class=DishkaRoute,
                        prefix="/fetch",
                        tags=["fetch"]
                        )


@fetch_router.get("/all")
async def fetch_all( fetcher: Annotated[Indexer, FromDishka()] ):
    try:
        logger.info("fetch di tutti i documenti")
        result = await fetcher.bulk_indexer()
        logger.debug("fetch eseguito")
        return {
            "status": "completed",
            "documents_indexed": result["success_count"],
            "errors": result["error_count"],
            "success": not result["has_errors"]
        }

    except Exception as e: 
        logger.error(f"end point fetch non riuscito: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Errore durante il fetch dei documenti"
        )

