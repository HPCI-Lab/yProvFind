from elasticsearch import AsyncElasticsearch
import logging
from settings import settings
import os
from utils.error_handlers import safe_es_call
import asyncio

logger = logging.getLogger(__name__)
#ricordare che anche elasticsearch ha il suo logger, per cambiare la sua configurazione bisogna fare logging.getLogger("elasticsearch") e cambiare la sua configurazione

BASE_DIR = os.path.dirname(__file__)

# In Docker, il certificato sarà montato in /app/certs
if os.path.exists('/app/certs/http_ca.crt'):
    logger.debug("caricato certificato da docker")
    CERTIFICATE_PATH = '/app/certs/http_ca.crt'
else:
    # Fallback per sviluppo locale
    logger.debug("caricato certificato da locale")
    CERTIFICATE_PATH = os.path.join(BASE_DIR, "http_ca.crt")


class ElasticSearchConnection: #classe per gestire la connessione a elasticsearch
    def __init__(self):
        self.host = settings.ELASTICSEARCH_URL
        self.client = None




    async def connect(self, attempts: int = 5, delay: int = 5): 
        if self.client is None: 
            for a in range (1, attempts):
                try:
                    logger.debug(f"tentaivo di connesione numero {a}")
                    self.client = AsyncElasticsearch(hosts=self.host,  
                                                    basic_auth=(settings.ES_USER, settings.ES_PASSWORD),
                                                    ca_certs=CERTIFICATE_PATH,  
                                                    verify_certs=True )
                    await safe_es_call(self.client.info(), "admin")
                    return 
                except (ConnectionError, Exception) as e:
                    logger.warning(f"Connessione a Elasticsearch fallita ({e}).")
                    if a < attempts:
                        wait = delay * a
                        logger.info(f"Riprovo tra {wait} secondi...")
                        await asyncio.sleep(wait)
                    else:
                        logger.error("Impossibile connettersi a Elasticsearch dopo vari tentativi.")
                        self.client = None
                        return  # <-- non solleva eccezione: avvia comunque FastAPI
                



    async def close(self):
        if self.client:
            await safe_es_call(self.client.close(), "admin")


    def get_client(self):
        if self.client is None:
            raise RuntimeError("Elasticsearch client is not connected. Call connect() first.")
        return self.client