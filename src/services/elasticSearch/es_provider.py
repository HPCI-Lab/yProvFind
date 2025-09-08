import logging
from settings import settings
from .es_connection import ElasticSearchConnection
from dishka import Provider, provide, Scope
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

class ElasticSearchService(Provider): #estensione della factory class Provider di dishka
    @provide(scope=Scope.APP) #lo scope è un decoratore di dishka, ci dice che il metodo è responsabile di creare una e restituire una istanza di risorse risorsa
                              #inoltre gestisce il ciclo di vita della risorsa, nel nostro caso con .APP la risorsa è viva finche app è viva
                              
    #qua specifichiamo il tipo da ritornare della funzione, ovvero un generatore asincrono che produce oggetti di tipo ElasticSearchConnection (il generatore è un iteratore)
    async def get_es_connection(self) ->AsyncGenerator [ElasticSearchConnection, None]: #dishka riceve il generatore e riconoce che gli restituisce un oggetto di tipo ElasticSearchConnection
        conn=ElasticSearchConnection(host=settings.ES_HOST) #qua diamo l'host al gestore della connessione() potrebbe essere anche una lista)
        try:
            await conn.connect()
            logger.info("ElasticSearch connection established")
            yield conn
        except Exception as e:
            logger.error(f"Failed to connect to ElasticSearch: {e}")
            raise
        finally:
            await conn.close()
            logger.info("ElasticSearch connection closed")
