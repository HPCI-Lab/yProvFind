from fastapi import FastAPI
from routers.root import root_routes
from services import providers
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.orchestration.SFEI_controller import SFEIController
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from settings import settings



logger = logging.getLogger(__name__)



scheduler = AsyncIOScheduler()

def create_lifespan(container):
    async def _run_sfei_init():
        
        async with container() as request_container:
            try:
                SFEI_controller = await request_container.get(SFEIController)
                await SFEI_controller.SFEI_init()
                logger.info("SFEI process successfully completed")
            except Exception as e:
                logger.exception(f"An error occurred during the SFEI process: {e}")
    
    async def _starter():
        """Esegue setup iniziale completo (solo all'avvio)"""
        async with container() as request_container:
            try:
                await request_container.get(ElasticSearchConnection)
                SFEI_controller = await request_container.get(SFEIController)
                await SFEI_controller.SFEI_init()
                logger.info("Starter successfully completed ")
            except Exception as e:
                logger.exception(f"Errore nello starter: {e}")
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger.info("Application launch - full startup in background")
        
        # Esegui starter completo solo all'avvio (con ElasticSearch check)
        asyncio.create_task(_starter())
        
        # Schedula solo SFEI_init (senza ElasticSearch check) ogni 4 ore
        scheduler.add_job(
            _run_sfei_init,
            'interval',
            hours=settings.SCHEDULER_INTERVAL_HOURS,
            #minutes=2,  # per test
            id='sfei_init_job',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info(f"Application ready - SFEI_init scheduled every {settings.SCHEDULER_INTERVAL_HOURS} hours")
        
        yield
        
        # Shutdown
        logger.info("Application Shutdown - scheduler shutdown")
        scheduler.shutdown(wait=True)
    
    return lifespan

def get_app():
    services = [provider() for provider in providers]
    container = make_async_container(*services)
    
    app = FastAPI(
        title="yProvFind",
        description="Federated Index and Discovery - yProv Provenance Lookup Service",
        version="1.0.0",
        lifespan=create_lifespan(container)
    )
    app.include_router(root_routes)
    setup_dishka(container=container, app=app)
    
    return app