import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from typing import Annotated, Optional
from services.orchestration.SFEI_controller import SFEIController
from pydantic import BaseModel
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

scraper_router = APIRouter(
    route_class=DishkaRoute,
    prefix="/fetch",
    tags=["fetch"]
)

SFEI_status = {
    "status": "idle",
    "details": "",
    "ES_successfully_indexed": 0,
    "ES_error_count": 0,
    "embed_success": 0,
    "embed_error": 0,
    "started_at": None,
    "completed_at": None
}


class ScraperStatusResponse(BaseModel):
    status: str  
    details: str
    ES_successfully_indexed: int
    ES_error_count: int
    embed_success: int
    embed_error: int
    started_at: Optional[str] = None  # ← Fixed: Optional[str] instead of str
    completed_at: Optional[str] = None  # ← Fixed: Optional[str] instead of str


@scraper_router.post("/start")
async def start_fetch(
    background_tasks: BackgroundTasks,
    SFEI_controller: Annotated[SFEIController, FromDishka()]
):
    """Start the fetch process (only if not already running)"""
    global SFEI_status
    
    # Check if a process is already running
    if SFEI_status["status"] == "running":
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
async def get_status():
    """Get the current process status"""
    global SFEI_status
    return SFEI_status


@scraper_router.post("/reset")
async def reset_status():
    """Reset state (only if not running)"""
    global SFEI_status
    
    if SFEI_status["status"] == "running":
        raise HTTPException(
            status_code=409,
            detail="Cannot reset: process is running"
        )
    
    SFEI_status = {
        "status": "idle",
        "details": "",
        "ES_successfully_indexed": 0,
        "ES_error_count": 0,
        "embed_success": 0,
        "embed_error": 0,
        "started_at": None,
        "completed_at": None
    }
    
    return {"message": "Status has been reset"}