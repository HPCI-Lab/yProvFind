from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ES_HOST: str
    ES_USER: str
    ES_PASSWORD: str
    INDEX_NAME: str = "documents"   
    

    PAGE: int = 0
    BATCH_SIZE: int = 5


    USE_LOCAL_EMBEDDER:bool= True

    class Config:
        env_file =".env"

settings = Settings()