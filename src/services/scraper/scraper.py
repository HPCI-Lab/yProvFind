import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from settings import settings
from typing import List, Dict
import asyncio
from settings import settings
from datetime import datetime

logger =logging.getLogger(__name__)

logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.INFO)



class ScraperService:
    """The scraper is the module that communicates with yProvStore to retrieve pages
      (or batches) of metadata that are then passed to the pipeline"""
    def __init__(self):
        self.semaphore=None
        self.client= httpx.AsyncClient() 

        
    #one page at a time of size BATCH_SIZE
    async def scraper_document_stream(self, base_url: str,last_fetch: str, page_size: int):
        page=0 

        while True:

            #page load
            documents_page = await self._fetch_page(base_url, page, page_size, last_fetch)
            
            if not documents_page:
                logger.info(f"No documet found in {base_url}, scraper stop.")
                break
                
            #retrive the metadata for each element of the page
            complete_doc_list= await self.complete_document(documents_page, base_url)

            #sending batches of metadata to the pipeline
            yield complete_doc_list

            #next page
            page += 1

            #if the list is terminated interrupt the process
            if len(documents_page) < page_size:
                break

        
    async def close(self):
        await self.client.aclose()

    @retry(
            stop=stop_after_attempt(3), 
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
            reraise=True
        )
    async def _fetch_page(self, base_url: str, page: int, page_size: int, update_after: str = None):
        """
        Retrieves a single page of metadata from a yProvStore instance.
        Implements retry logic with exponential backoff to handle network instability.
        """
        url = f"{base_url}/documents"
        params = {"page": page, "page_size": page_size}

        #Added time filter to avoid recovering previously indexed documents
        if update_after:
            params["updated_after"] = update_after

        response = await self.client.get(url, params=params)
        response.raise_for_status() #raise exception if the status code is not 2xx
        return response.json()


    async def complete_document(self, batch: List[Dict], base_url: str):
        tasks = []
        
        logger.debug(f"Fetching metadata for: {base_url}")
        for doc in batch:
            pid = doc.get("pid")
            tasks.append(self._fetch_metadata(base_url, pid)) #per ogni documento facciamo chiamata metadati in parallelo, grazie poi a semaphore non saturiamo la rete
        
        try:
            # return_exceptions=True: non fallisce se alcuni metadata falliscono
            metadatas = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_metadata = sum(1 for m in metadatas if not isinstance(m, Exception))
            logger.info(f"Metadata retrieved: {successful_metadata}/{len(metadatas)} for {base_url}")
            
            results = []
            #v1_list={} #ritorno id dei parenti pid di tutti i documenti che hanno versione 2 perche deve essere modificata la lineage dei loro parent pid
            for doc, metadata in zip(batch, metadatas):
                # Se metadata è un'eccezione, usa valori vuoti
                if isinstance(metadata, Exception):
                    logger.warning(f"Metadata failed for {doc.get('pid')}: {metadata}")
                    metadata = {"title": "", "description": "", "keywords": "", "author":""}  # metadata vuoti
                

                if  doc.get("lineage_id") is None or doc.get("lineage_id") == "":
                    lineage_value= f"standalone_{doc["pid"]}"
                else:
                    lineage_value=  doc.get("lineage_id") 

                #i campi con _ davanti servono ad elasticsearch come istruzioni, non togliere
                #i campi dentro _source sono quelli invece effettivamente indicizzati
                #la mappatura dell'indice si riferisce esclusivamente ai campi dentro _source
                complete_doc = {
                    "_index": settings.INDEX_NAME,
                    "_id": doc["pid"],
                    "_source": {
                        "pid": doc["pid"],
                        "version": doc["version"], 
                        "owner_email": doc["owner_email"],
                        "storage_url": doc["storage_url"],
                        "parent_document_pid": doc["parent_document_pid"],
                        "lineage":lineage_value,

                        "title": metadata.get("title", None),
                        "description": metadata.get("description", None),
                        "keywords": metadata.get("keywords", None),
                        "author": metadata.get("author", None),

                        "created_at": datetime.utcnow().isoformat(),
                        "yProvIstance": base_url

                        
                    },
                }


                results.append(complete_doc)
            
            return results
            
        except Exception as e:
            logger.error(f"Critical error in complete_document for {base_url}: {e}")
            # Restituisci documenti con metadata vuoti invece di fallire tutto
            return [{
                "_index": settings.INDEX_NAME,
                "_source": {
                    "pid": doc["pid"],
                    "version": doc["version"],
                    "owner_email": doc["owner_email"], 
                    "parent_document_pid": doc["parent_document_pid"],
                    "title": None, "description": None, "keywords": None, "author": None
                }
            } for doc in batch]
        

    async def _fetch_metadata(self, base_url: str, pid: str):
         
        url = f"{base_url}/documents/{pid}/metadata"

        #creare i semaphore solo dentro un loop asincrono gia attivo o da errore
        if self.semaphore is None:
            self.semaphore=asyncio.Semaphore(5)

        async with self.semaphore: 
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.ReadTimeout:
                logger.warning(f"Timeout {url}")
                return {}
            except Exception as e:
                logger.error(f"scraper error during the retrive of metadata: {e}")
                return{}











"""""

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
"""


    


            



