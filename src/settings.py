from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    ELASTICSEARCH_URL: str
    ES_USER: str
    ES_PASSWORD: str
    INDEX_NAME: str = "documents"   

    USE_ENRICHER_LLM: bool = True
    
    

    PAGE: int = 0
    BATCH_SIZE: int = 5


    USE_LOCAL_EMBEDDER:bool= False

    SCHEDULER_INTERVAL_HOURS: int = 4 

    STAC_BASE_PATH: str = "STAC"

    REGISTRY_BASE_PATH : str = "registryList"
    REGISTRY_FILE_NAME: str = "registryList.json"

    OPENAI_API_KEY: Optional[str] = None
    OPEN_ROUTER: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY:str

    OLLAMA_URL: str = "http://host.docker.internal:11434/api/chat"
    OLLAMA_MODEL: str = "qwen3.5:0.8b"

    class Config:
        env_file =".env"

settings = Settings()