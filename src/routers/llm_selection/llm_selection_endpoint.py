from fastapi import APIRouter, Body, Query
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from services.LLM.llm import LlmHandler
from typing import Annotated
from pydantic import BaseModel, Field, field_validator


llm_router=APIRouter(route_class=DishkaRoute,
                     prefix="/llm",
                     tags=["LLM"])



class LlmSelectionInput(BaseModel):
    provider: str = Field(..., example="groq", description="The name of the provider (es. groq, openrouter, gemini)")
    model: str = Field(..., example="llama-3.3-70b-versatile", description="The name of the LLM model")
    key: str = Field(..., example="gsk_...", description="User API key")

    @field_validator("provider", "model", "key")
    @classmethod
    def strip_and_require_non_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("The field cannot be empty or contain only spaces")
        return cleaned

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, v: str) -> str:
        return v.lower()



        
@llm_router.put("/select", description="Select the provider, the llm model and the key")
async def select_llm(data: LlmSelectionInput, llm_manager: Annotated[LlmHandler, FromDishka()]):
    
    llm_manager.update_config_llm(
        provider=data.provider,
        model=data.model,
        key=data.key
    )
    
    return {
        "status": "success", 
        "message": f"Successfully configured on {data.provider} with the {data.model} model"
    }