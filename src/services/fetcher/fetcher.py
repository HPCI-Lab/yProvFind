import logging
import httpx
from dishka import Provider, provide, Scope
from settings import settings
import json
import aiofiles
from typing import List, Dict
import asyncio
from settings import settings
import os
FOLDER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "jsonDoc")

logger =logging.getLogger(__name__)

logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.INFO)


class DocumentFetcher:
    def __init__(self):
        self.semaphore=asyncio.Semaphore(4)
        self.client= httpx.AsyncClient() #creo qua il client cosi la connessione è persistente


    


    async def fetch_document_stream(self, base_url: str, batch_size: int =  settings.BATCH_SIZE ):
        page=0
        page_size=settings.PAGE_SIZE

        while True:
            # Carica solo UNA pagina alla volta
            documents_page = await self._fetch_page(base_url, page, page_size)
            
            if not documents_page:
                break
                
            complete_doc_list= await self.complete_document(documents_page, base_url)

            
            # con yield appena arriva la prima pagina gia si puo iniziare a processare i documenti, mentre se fosse stata implementata 
            # una lista che accumulava avremmo dovuto attendere il caricamento di tutte le pagine prima
            yield complete_doc_list

                
            page += 1
            if len(documents_page) < page_size:
                break
        

    async def _fetch_page(self, base_url: str, page: int = settings.PAGE, page_size: int= settings.PAGE_SIZE):
        url = f"{base_url}/documents"
        params = {"page": page, "page_size": page_size}
        
        # Usa httpx async
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
    
    async def _fetch_metadata(self, base_url: str, pid: str):
         
        url = f"{base_url}/documents/{pid}/metadata"
        async with self.semaphore: 
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.ReadTimeout:
                logger.warning(f"Timeout {url}")
                return {}
            except Exception as e:
                logger.error(f"errore nel recuperare i metadati: {e}")
                return{}
        

    async def complete_document(self, batch: List[Dict], base_url: str):
        tasks = []
        
        logger.info(f"Fetching metadata for: {base_url}")
        for doc in batch:
            pid = doc.get("pid")
            #logger.debug(f"Fetching metadata for:{base_url}___{pid}")
            tasks.append(self._fetch_metadata(base_url, pid))

        metadatas = await asyncio.gather(*tasks)
        logger.notice(f"Metadata found :{len(metadatas)} for {base_url}")
        

        results = []
        for doc, metadata in zip(batch, metadatas):
            complete_doc = {
                "_index": settings.INDEX_NAME,
                "_source": {
                    "pid": doc["pid"],
                    "version": doc["version"],
                    "owner_email": doc["owner_email"],
                    "parent_document_pid": doc["parent_document_pid"],
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "keywords": metadata["keywords"],
                    "author": metadata["author"],
                },
            }
            results.append(complete_doc)

        return results
        















    async def fetch_documents_async(self):
        logger.debug("documents loaded from local directory")
        for filename in os.listdir(FOLDER_PATH):
            if filename.endswith(".json"):
                filepath = os.path.join(FOLDER_PATH, filename)
                async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
                    content = await f.read()
                    doc = json.loads(content)
                    
                    yield {"_index": settings.INDEX_NAME, "_source": doc}   #posso usare i generator con elastic search perche che sia una lista o un generator essi fanno parte della sottocategoria di iterator                                                        
                                                                        #e le api bulk di elasticsearch accettano qualsiasi iteratore e quindi anche un generator va bene
                                                                        #questo è utile perche con i generator non c'è da salvare in memoria una lista ma funziona poco alla volta e quindi scalabile anche su migliaia di file



    


            



