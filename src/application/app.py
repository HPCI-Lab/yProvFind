from fastapi import FastAPI
from routers.root import root_routes
from services import providers
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.document_fetcher.indexer import Indexer
import logging

logger = logging.getLogger(__name__)

def get_app():
    app=FastAPI()
    app.include_router(root_routes)


    #carichiamo i servizi (provider) nel container di dishka, e lo colleghiamo a FastAPI
    #nel momento che si caricano i servizi non vengono anche eseguiti, essi si attivano solo se chiamati e ignettati da dishka
    services = [provider() for provider in providers]
    container = make_async_container(*services)
    setup_dishka(container=container, app=app)


    @app.on_event("startup") #forziamo la connessione ad elastichsearch all'avvio
    async def startup_event():
        
        async with container() as request_container: #la funzione container() ci restituisce un context manager per interagire con il container 
            await request_container.get(ElasticSearchConnection) #attiviamo la connessione ad elastichSearch (se non va crasha)

            #a connessione stabilita indicizziamo tutti i file presi da yProvStore e li indicizziamo in elastic Search
            indexer = await request_container.get(Indexer)
            await indexer.bulk_indexer()#qua viene avviata
            

    return app