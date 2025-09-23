from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ES_HOST: str
    ES_USER: str
    ES_PASSWORD: str
    INDEX_NAME: str = "documents"   
    

    PAGE: int = 0
    PAGE_SIZE: int = 100
    BATCH_SIZE: int = 100

    class Config:
        env_file =".env"

settings = Settings()