import uvicorn
from application.app import get_app
from loggin.logging_config import setup_logging
import logging

app = get_app()

setup_logging(level=logging.DEBUG)
logger= logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("logger on DEBUG")
    uvicorn.run(
        app=app,
        port=8001,
        reload=False
    )