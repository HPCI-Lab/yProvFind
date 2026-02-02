from pydantic_settings import BaseSettings

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

    OPENAI_API_KEY:str
    OPEN_ROUTER:str
    GEMINI_API_KEY:str
    GROQ_API_KEY:str

    class Config:
        env_file =".env"

settings = Settings()