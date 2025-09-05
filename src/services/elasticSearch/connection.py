from elasticsearch import AsyncElasticsearch
from loggin.logging_config import get_logger


logger = get_logger(__name__)


class ElasticSearchConnection: #classe per gestire la connessione a elasticsearch
    def __init__(self, host):
        self.host = host
        self.client = None

    async def connect(self):
        logger.debug("Chiamata connect()")
        if self.client is None:
            logger.debug("Connecting to Elasticsearch...")
            self.client = AsyncElasticsearch(hosts=self.host,
                                             basic_auth=("elastic", "3_rc51nu6W0lGEf*Mj-P"),
                                            verify_certs=False) #qua non inizia la connessione ma settiamo solo l'host (volendo host puo essere una lista di host)
            try:
                await self.client.info()
                
            except Exception as e: 
                logger.error(f"Errore connessione elasticsearch: {e}")
                self.client = None
                raise
    
    async def close(self):
        if self.client:
            await self.client.close()

    def get_client(self):
        if self.client is None:
            raise RuntimeError("Elasticsearch client is not connected. Call connect() first.")
        return self.client