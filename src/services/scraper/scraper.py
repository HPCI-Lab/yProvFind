import logging
import httpx
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
    def __init__(self):
        self.semaphore=asyncio.Semaphore(4)
        self.client= httpx.AsyncClient() #creo qua il client cosi la connessione è persistente

        

    async def fetch_document_stream(self, base_url: str,last_fetch: str, page_size: int =  settings.BATCH_SIZE ):
        page=0 

        while True:
            # Carica solo UNA pagina alla volta
            documents_page = await self._fetch_page(base_url, page, page_size, last_fetch)
            
            if not documents_page:
                logger.info(f"No documet found in {base_url}, scraper stop.")
                break
                
            #complete_doc_list, v2_list= await self.complete_document(documents_page, base_url)
            complete_doc_list= await self.complete_document(documents_page, base_url)
            # con yield appena arriva la prima pagina gia si puo iniziare a processare i documenti, mentre se fosse stata implementata 
            # una lista che accumulava avremmo dovuto attendere il caricamento di tutte le pagine prima
            yield complete_doc_list#, v2_list

            page += 1
            if len(documents_page) < page_size:
                break

        
    async def close(self):
        await self.client.aclose()


    async def _fetch_page(self, base_url: str, page: int , page_size: int, update_after: str = None ):
        url = f"{base_url}/documents"
        params = {"page": page, "page_size": page_size}
        if update_after:
            params["updated_after"]= update_after
        # Usa httpx async
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status() #se la risposta non è 200 fa raise
            return response.json()
        except Exception as e:
            logger.error(f"load page error: {e}")
            return{}  #se avviene un errore con una pagina si ritorna pagina vuota e non blocca il resto
        
    


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
            v1_list={} #ritorno id dei parenti pid di tutti i documenti che hanno versione 2 perche deve essere modificata la lineage dei loro parent pid
            for doc, metadata in zip(batch, metadatas):
                # Se metadata è un'eccezione, usa valori vuoti
                if isinstance(metadata, Exception):
                    logger.warning(f"Metadata failed for {doc.get('pid')}: {metadata}")
                    metadata = {"title": "", "description": "", "keywords": "", "author":""}  # metadata vuoti
                
                """
                #creazione lista per aggiornare la lineage delle versioni 1 con l'indicizzazione della versione 2
                if doc["version"]==2 and doc.get("parent_document_pid"):
                    v1_list[doc["parent_document_pid"]]= doc["lineage_id"]
                """
                if  doc.get("lineage_id") is None or doc.get("lineage_id") == "":
                    lineage_value= f"standalone_{doc["pid"]}"
                else:
                    lineage_value=  doc.get("lineage_id") 

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
                        "title": metadata.get("title", ""),
                        "description": metadata.get("description", ""),
                        "keywords": metadata.get("keywords", ""),
                        "author": metadata.get("author",""),
                        
                        "created_at": datetime.utcnow().isoformat(),
                        "yProvIstance": base_url
                    },
                }


                results.append(complete_doc)
            
            return results#, v1_list
            
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
                    "title": "", "description": "", "keywords": "", "author": ""
                }
            } for doc in batch]
        

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


    


            



