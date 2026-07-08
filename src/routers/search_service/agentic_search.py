import logging
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from services.elasticSearch.search_service.agentic_search import AgenticSearch
from typing import Annotated 

logger = logging.getLogger(__name__)

agent_router = APIRouter(
    route_class=DishkaRoute,
    prefix="/search",
    tags=["Search"]
)

class AgenticSearchResponse(BaseModel):
    agent_response: str
    raw_results: List[Dict[str, Any]]


@agent_router.get("/agentic",     
                  summary="Run an AI-driven agentic search utilizing local Ollama reasoning",
                  description="This endpoint extracts structured database filters from natural language queries via local LLM processing, performs a rigorous Elasticsearch retrieval, and uses the model to synthesize a human-readable response.",
                  response_description="A structured model combining the conversational answer and the raw query tracking results.",
                  response_model=AgenticSearchResponse
                 )
async def search_agentic(
    agentic_search: Annotated[AgenticSearch, FromDishka()],
    query: str = Query(..., description="Your natural language question for the AI agent (e.g., 'Find version 2 documents matching climate data from 2024')")
) -> AgenticSearchResponse:
    
    logger.info(f"Routing natural query to agent: {query}")
    # Invoke the search orchestration method inside your agentic search file
    result = await agentic_search.search(user_prompt=query)
    return result