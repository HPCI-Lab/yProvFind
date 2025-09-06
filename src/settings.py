from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ES_HOST: str
    ES_USER: str
    ES_PASSWORD: str

    class Config:
        env_file =".env"

settings = Settings()