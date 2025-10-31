import uvicorn
from application.app import get_app
from application.logging_config import setup_logging
import logging

app = get_app()

setup_logging(level=logging.INFO)
logger= logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("logger on DEBUG")
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8002,
        reload=False
    )