from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ELASTICSEARCH_URL: str
    ES_USER: str
    ES_PASSWORD: str
    INDEX_NAME: str = "documents"   
    

    PAGE: int = 0
    BATCH_SIZE: int = 5


    USE_LOCAL_EMBEDDER:bool= False

    SCHEDULER_INTERVAL_HOURS: int = 4 

    STAC_BASE_PATH: str = "STAC"

    REGISTRY_BASE_PATH : str = "registryList"
    REGISTRY_FILE_NAME: str = "registryList.json"

    class Config:
        env_file =".env"

settings = Settings()