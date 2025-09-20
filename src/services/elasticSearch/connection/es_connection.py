from elasticsearch import AsyncElasticsearch
import logging
from settings import settings
import os
from utils.error_handlers import safe_es_call

logger = logging.getLogger(__name__)
#ricordare che anche elasticsearch ha il suo logger, per cambiare la sua configurazione bisogna fare logging.getLogger("elasticsearch") e cambiare la sua configurazione

BASE_DIR= os.path.dirname(__file__)
CERTIFICATE_DIR= os.path.join(BASE_DIR, "http_ca.crt")


class ElasticSearchConnection: #classe per gestire la connessione a elasticsearch
    def __init__(self, host):
        self.host = host
        self.client = None

    async def connect(self):
        if self.client is None:
            logger.debug("Creating new Elasticsearch client...")
            self.client = AsyncElasticsearch(hosts=self.host,
                                            basic_auth=(settings.ES_USER, settings.ES_PASSWORD),
                                            ca_certs=CERTIFICATE_DIR) #qua non inizia la connessione ma settiamo solo l'host (volendo host puo essere una lista di host)
            
            await safe_es_call(self.client.info(), "admin")
            
    async def close(self):
        if self.client:
            await safe_es_call(self.client.close(), "admin")

    def get_client(self):
        if self.client is None:
            raise RuntimeError("Elasticsearch client is not connected. Call connect() first.")
        return self.client