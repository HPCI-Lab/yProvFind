from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ES_HOST: str
    ES_USER: str
    ES_PASSWORD: str
    INDEX_NAME: str = "documents"   

    class Config:
        env_file =".env"

settings = Settings()