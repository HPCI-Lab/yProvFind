from fastapi import FastAPI
from routers.root import root_routes
from services import providers
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.indexer.indexer import IndexService
from services.orchestration.SFEI_controller import SFEIController
import logging
import asyncio

logger = logging.getLogger(__name__)

def get_app():
    app=FastAPI(title="yProvSearch",
                description="Servizio di ricerca provenance all'interno di yProvStore",
                version="1.0.0"
                )
    app.include_router(root_routes)


    #carichiamo i servizi (provider) nel container di dishka, e lo colleghiamo a FastAPI
    #nel momento che si caricano i servizi non vengono anche eseguiti, essi si attivano solo se chiamati e ignettati da dishka
    services = [provider() for provider in providers]
    container = make_async_container(*services)
    setup_dishka(container=container, app=app)


    async def _starter():
        async with container() as request_container:
            try:
                await request_container.get(ElasticSearchConnection)
                """"
                
                await indexer.bulk_indexer_embeddings()
                #
                """
                SFEI_controller= await request_container.get(SFEIController)
                await SFEI_controller.SFEI_init()
                indexer= await request_container.get(IndexService)
                await indexer.check_current_mapping()

            except Exception as e:
                logger.exception(f"errore nello starter {e}")
        




    @app.on_event("startup")
    async def startup_event():
        # Crea la task ma NON aspettarla
        task = asyncio.create_task(_starter())
        
        # Opzionale: salva il task per poterlo cancellare dopo
        app.state.background_task = task
        
        logger.info("✅ FastAPI avviato, background task in corso...")
        # startup_event() finisce subito → FastAPI diventa ready

    @app.on_event("shutdown") 
    async def shutdown_event():
        # Cancella gracefully il background task
        if hasattr(app.state, 'background_task'):
            app.state.background_task.cancel()
            

    return app