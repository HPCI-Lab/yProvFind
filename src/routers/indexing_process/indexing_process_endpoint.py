import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from typing import Annotated, Optional
from services.orchestration.RSEI_controller import RSEIController
from pydantic import BaseModel
from datetime import datetime
from services.orchestration.RSEI_status import RSEIStatus
import asyncio

logger = logging.getLogger(__name__)

indexing_process = APIRouter(
    route_class=DishkaRoute,
    prefix="/indexing-process",
    tags=["Indexing process"]
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


@indexing_process.post("/start")
async def start_indexing_process(
    
    background_tasks: BackgroundTasks,
    RSEI_controller: Annotated[RSEIController, FromDishka()],
    process_status: Annotated[RSEIStatus, FromDishka()]  ,
    batch_delay: Optional[int] = Query(0, 
                                        ge=0, # Greater or equal to 0
                                        le=3600, #limite massimo di un'ora per sicurezza
                                        description="Allows you to insert a delay between one batch and another in seconds"),
    batch_size: Optional[int] = Query(5,
                                    ge=1, # Greater or equal to 1
                                    le=50, # batch non piu grandi di 50 per non sovracaricare il sistema 
                                    description="allows you to decide the size of the provenace documents batch to process"),
    use_enricher: bool = Query(True, description="If it is True use the enricher that call the llm to enrich the metadata")
):
    """
    Initiates the indexing and semantic enrichment process for provenance documents.

    The endpoint triggers an asynchronous pipeline that performs the following steps:
    1. **Status Verification**: Ensures no other indexing process is currently active to prevent data inconsistency.
    2. **Background Execution**: Offloads the procedure to the RSEI controller using FastAPI's BackgroundTasks, allowing an immediate HTTP response.
    3. **Batch & Rate Management**: 
    - Segments the document stream into chunks defined by `batch_size`.
    - Implements a `batch_delay` (starting from the second batch) to respect external LLM API quotas and manage Elasticsearch indexing pressure.
    4. **Enrichment Logic and Metadata Constraints**:
    - **With Enricher (True)**: The LLM generates semantic descriptions and keywords, ensuring every document is correctly indexed with some metadata.
    - **Without Enricher (False)**: The system only indexes documents that *already* contain valid metadata. **Documents lacking metadata will be skipped**, as the system requires semantic information for accurate vector indexing.
    
    

    **Critical Recovery Information:**
    If documents are skipped due to missing metadata, the process will not automatically retry them. To index these files later (e.g., after enabling the enricher), the user must manually restart the indexing process and update the **last_fetch timestamp** of the specific source instance to a date prior to the skipped files' creation.

    **Control Parameters:**
    - **batch_delay**: Essential for 'Rate Limiting' to avoid 429 errors from LLM providers.
    - **batch_size**: Optimizes the balance between memory usage and throughput.
    - **use_enricher**: Determines the semantic depth of the index. Note that disabling this may result in fewer documents being indexed if source metadata is sparse.

    **Responses:**
    - **200 OK**: Process started successfully.
    - **409 Conflict**: A process is already running.
    - **500 Internal Server Error**: Unexpected error during initialization.
    """
    
    # Check if a process is already running
    if process_status.is_running():
        raise HTTPException(
            status_code=409,
            detail="A process is already running. Please wait for it to complete."
        )
    
    try:
        logger.info("Starting indexing process")
        
        # Start the process in background
        background_tasks.add_task(RSEI_controller.RSEI_init, batch_delay, batch_size, use_enricher)
        
        return {
        "message": f"Process started successfully with a batch size of: {batch_size} and a delay for each batch of {batch_delay}",
        "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Failed to start indexing process: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting indexing process: {e}"
        )


@indexing_process.get("/status", response_model=ScraperStatusResponse)
async def get_status( process_status: Annotated[RSEIStatus, FromDishka()] ):
    """Get the current process status"""
    return process_status.to_dict()


@indexing_process.post("/reset")
async def reset_status(process_status: Annotated[RSEIStatus, FromDishka()] ):
    """Reset state (only if not running)"""
    
    if process_status.is_running():
        raise HTTPException(
            status_code=409,
            detail="Cannot reset: process is running"
        )
    
    await process_status.reset()
    
    return {"message": "Status has been reset"}



@indexing_process.delete("/abort")
def abort(process_status: Annotated[RSEIStatus, FromDishka()], RSEI_controller: Annotated[RSEIController, FromDishka()], ):
    """ Terminate the indexing process """
    if not process_status.is_running():
        raise HTTPException(
            status_code=409,
            detail="There is no process to abort"
        )
    RSEI_controller.abort()
    return {"message": "Process aborted, please wait for the current batch to finish"}

@indexing_process.get("/errors")
async def get_errors_list(RSEI_controller: Annotated[RSEIController, FromDishka()]):
    """Show the errors occurred during the indexing process"""
    return await RSEI_controller.get_errors_list()
    