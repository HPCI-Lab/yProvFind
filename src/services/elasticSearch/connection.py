from elasticsearch import AsyncElasticsearch
from loggin.logging_config import get_logger


logger = get_logger(__name__)


class ElasticSearchConnection: #classe per gestire la connessione a elasticsearch
    def __init__(self, host):
        self.host = host
        self.client = AsyncElasticsearch | None

    async def connect(self):
        if self.client is None:
            self.client = AsyncElasticsearch(hosts=self.host) #qua non inizia la connessione ma settiamo solo l'host (volendo host puo essere una lista di host)
            try:
                await self.client.info()
                logger.info("Connected to Elasticsearch")
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