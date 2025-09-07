from elasticsearch import AsyncElasticsearch
import logging
from settings import settings

logger = logging.getLogger(__name__)
#ricordare che anche elasticsearch ha il suo logger, per cambiare la sua configurazione bisogna fare logging.getLogger("elasticsearch") e cambiare la sua configurazione


class ElasticSearchConnection: #classe per gestire la connessione a elasticsearch
    def __init__(self, host):
        self.host = host
        self.client = None

    async def connect(self):
        if self.client is None:
            logger.debug("Creating new Elasticsearch client...")
            self.client = AsyncElasticsearch(hosts=self.host,
                                             basic_auth=(settings.ES_USER, settings.ES_PASSWORD),
                                            verify_certs=False) #qua non inizia la connessione ma settiamo solo l'host (volendo host puo essere una lista di host)
            try:
                await self.client.info()
                logger.debug("Elasticsearch client connected successfully.") #viene scritto solo se await non fallisce 
                
            except Exception as e: 
                logger.error(f"ElastichSearch connection error: {e}")
                self.client = None
                raise #se non si connette fa fallire lo startup e crash l'app chiudendo fastAPI
    
    async def close(self):
        if self.client:
            await self.client.close()

    def get_client(self):
        if self.client is None:
            raise RuntimeError("Elasticsearch client is not connected. Call connect() first.")
        return self.client