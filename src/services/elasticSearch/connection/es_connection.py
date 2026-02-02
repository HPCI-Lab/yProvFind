from elasticsearch import AsyncElasticsearch
import logging
from settings import settings
import os
from utils.error_handlers import safe_es_call
import asyncio


logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(__file__)

# In Docker, il certificato sarà montato in /app/certs
if os.path.exists('/app/certs/http_ca.crt'):
    logger.debug("caricato certificato da docker")
    CERTIFICATE_PATH = '/app/certs/http_ca.crt'
else:
    logger.debug("caricato certificato da locale")
    CERTIFICATE_PATH = os.path.join(BASE_DIR, "http_ca.crt")

 
class ElasticSearchConnection: #classe per gestire la connessione a elasticsearch
    def __init__(self):
        self.host = settings.ELASTICSEARCH_URL
        self.client = None




    async def connect(self, attempts: int = 5, delay: int = 12): 
        if self.client is None: 
            for a in range(1, attempts + 1):
                try:
                    logger.debug(f"connection attempt {a}/{attempts}")
                    self.client = AsyncElasticsearch(
                        hosts=self.host,  
                        basic_auth=(settings.ES_USER, settings.ES_PASSWORD),
                        max_retries=1, 
                        #ca_certs=CERTIFICATE_PATH,  
                        verify_certs=False
                    )
                    await safe_es_call(self.client.info(), "admin")
                    logger.info(f"Elasticsearch connected successfully on attempt {a}")
                    await self.create_first_index()
                    return
                except (ConnectionError, Exception) as e:
                    logger.warning(f"Elasticsearch connection failed (attempt {a}/{attempts}): {e}")

                    
                    if self.client is not None:
                        try:
                            await self.client.close()
                        except Exception as close_err:
                            logger.debug(f"Error while closing ES client: {close_err}")
                        finally:
                            self.client = None

                    
                    if a < attempts:
                        
                        logger.info(f"Retry in {delay} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Elasticsearch connection failed after {attempts} attempts")
                        return

    

    async def close(self):
        if self.client:
            await safe_es_call(self.client.close(), "admin")


    def get_client(self):
        if self.client is None:
            raise RuntimeError("Elasticsearch client is not connected. Call connect() first.")
        return self.client
    

    async def create_first_index (self):
        index_name= settings.INDEX_NAME
        mapping={
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "analysis": {
                "tokenizer": {
                    "edge_ngram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 3,
                    "max_gram": 10,
                    "token_chars": ["letter", "digit"]
                    }
                },
                "analyzer": {
                    "edge_ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_tokenizer",
                    "filter": ["lowercase"]
                    }
                }
                }
            },
            "mappings": {
                "properties": {
                "pid": {
                    "type": "text",
                    "fields": {
                    "keyword": {"type": "keyword"}
                    }
                },
                "version": {
                    "type": "integer"
                },
                "owner_email": {
                    "type": "keyword"
                },
                "storage_url": {
                    "type": "keyword"
                },
                "parent_document_pid": {
                    "type": "keyword"
                },
                "lineage": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                    "keyword": {
                        "type": "keyword"
                    },
                    "ngram": {
                        "type": "text",
                        "analyzer": "edge_ngram_analyzer",
                        "search_analyzer": "standard"
                    }
                    }
                },
                "description": {
                    "type": "text"
                },
                "llm_description":{
                    "type": "text"
                },
                "keywords": {
                    "type": "text",
                    "fields": {
                    "ngram": {
                        "type": "text",
                        "analyzer": "edge_ngram_analyzer",
                        "search_analyzer": "standard"
                    }
                    }
                },
                "author": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                    }
                },
                "semantic_embedding": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine",
                    "index_options": {
                    "type": "int8_hnsw",
                    "m": 16,
                    "ef_construction": 100
                    }
                },
                "created_at": {
                    "type": "date"
                },
                "yProvIstance": {
                    "type": "keyword"
                }
                }
            }
            }
        try:
            exists = await self.client.indices.exists(index=index_name)
            
            if not exists:
                # AGGIUNGI await QUI
                await self.client.indices.create(index=index_name, body=mapping)
                logger.info("First index created")
            else:
                logger.debug("indice già presente")
        except Exception as e:
            logger.error(f"errore nella creazione del primo indice: {e}")
            return
            
        



