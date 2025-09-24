import logging 
from typing import List, Dict, Any
import asyncio
import httpx
logger = logging.getLogger(__name__)

class ScraperService(): 
    def __init__ (self):
        self.timeout = 5.0
        self.active_list: List[str] = []
        self.all_list: List[str]= ["http://127.0.0.1:8000",
                                    "http://192.168.1.245:8000"]
        

    async def getList(self) -> List[str]:
        await self.check_avaibility()
        return self.active_list
    
    async def check_avaibility(self):
        self.active_list=[]
        
        tasks= [self.health_check(address)
               for address in self.all_list]
        
        results = await asyncio.gather (*tasks, return_exceptions=True)

        for address, result in zip (self.all_list , results):
            #logger.debug(f"TIPO active_list: {type(self.active_list)} - VALORE: {self.active_list}")
            if result is True:  # Servizio attivo
                self.active_list.append(address)
                logger.notice(f"Scraper: Server address -> {address} -> ACTIVE")
            elif isinstance(result, Exception):
                logger.warning(f"Scraper: Server address -> {address} -> ERROR: {result}")
            else:
                logger.warning(f"Scraper: Server address -> {address} -> NOT RESPONDING")
        




    async def health_check(self, address: str)-> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{address}/status")

                if response.status_code==200:
                    message = response.json()
                    if message.get("status")=="ok":
                        return True
                logger.debug(f"status:{address} - Status: {response.status_code} ")
                return False

        except httpx.TimeoutException:
            logger.debug(f" {address} - TIMEOUT")
            return False
        except httpx.ConnectError:
            logger.debug(f" {address} - CONNECTION ERROR")
            return False
        except Exception as e:
            logger.debug(f" {address} - ERRORE: {e}")
            return False





