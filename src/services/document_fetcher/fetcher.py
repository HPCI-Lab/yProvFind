import logging
import httpx
from dishka import Provider, provide, Scope
from settings import settings
import json
import aiofiles

import os
FOLDER_PATH = os.path.join('..', 'jsonDoc')
INDEX_NAME = settings.INDEX_NAME




logger =logging.getLogger(__name__)

class DocumentFetcher:

    async def bulk_fetch(self, url: str):
        logger.debug("Fetching bulk documents")





    async def single_fetch(self, url: str):
        logger.debug("Fetching single document")

         
    async def fetch_documents_async(self):
        for filename in os.listdir(self.folder_path):
            if filename.endswith(".json"):
                filepath = os.path.join(self.folder_path, filename)
                async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
                    content = await f.read()
                    doc = json.loads(content)
                    yield {"_index": self.index_name, "_source": doc}   #posso usare i generator con elastic search perche che sia una lista o un generator essi fanno parte della sottocategoria di iterator                                                        
                                                                        #e le api bulk di elasticsearch accettano qualsiasi iteratore e quindi anche un generator va bene
                                                                        #questo è utile perche con i generator non c'è da salvare in memoria una lista ma funziona poco alla volta e quindi scalabile anche su migliaia di file



    


            



