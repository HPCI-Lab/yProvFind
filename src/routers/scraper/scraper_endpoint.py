import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from typing import Annotated, Optional
from services.orchestration.RSEI_controller import RSEIController
from pydantic import BaseModel
from datetime import datetime
from services.orchestration.RSEI_status import RSEIStatus
import asyncio

logger = logging.getLogger(__name__)

scraper_router = APIRouter(
    route_class=DishkaRoute,
    prefix="/fetch",
    tags=["Scraper"]
)


class ScraperStatusResponse(BaseModel):
    status: str  
    details: str
    ES_successfully_indexed: int
    ES_error_count: int
    embed_success: int
    embed_error: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@scraper_router.post("/start")
async def start_fetch(
    background_tasks: BackgroundTasks,
    SFEI_controller: Annotated[RSEIController, FromDishka()],
    process_status: Annotated[RSEIStatus, FromDishka()]  
):
    """Start the fetch process (only if not already running)"""
    
    # Check if a process is already running
    if process_status.is_running():
        raise HTTPException(
            status_code=409,
            detail="A process is already running. Please wait for it to complete."
        )
    
    try:
        logger.info("Starting document fetching process")
        
        # Start the process in background
        background_tasks.add_task(SFEI_controller.SFEI_init)
        
        return {
            "message": "Process started successfully",
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Failed to start scraper: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting process: {e}"
        )


@scraper_router.get("/status", response_model=ScraperStatusResponse)
async def get_status(
    process_status: Annotated[RSEIStatus, FromDishka()]  # ← Injected
):
    """Get the current process status"""
    return process_status.to_dict()


@scraper_router.post("/reset")
async def reset_status(
    process_status: Annotated[RSEIStatus, FromDishka()]  # ← Injected
):
    """Reset state (only if not running)"""
    
    if process_status.is_running():
        raise HTTPException(
            status_code=409,
            detail="Cannot reset: process is running"
        )
    
    await process_status.reset()
    
    return {"message": "Status has been reset"}