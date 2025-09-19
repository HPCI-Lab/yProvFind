import uvicorn
from application.app import get_app
from loggin.logging_config import setup_logging
import logging

app = get_app()

setup_logging(level=logging.INFO)

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        port=8001,
        reload=False
    )