import logging 
from typing import List, Dict, Any
import asyncio
import httpx
from fastapi import HTTPException
from settings import settings
from pathlib import Path
import json
import os

logger = logging.getLogger(__name__)

class RegistryService(): 
    """
        Il registry gestisce la lista di indirizzi yPorvStore, la lista viene salvata anche in memoria 
        il salvataggio su disco è sincrono, le operazioni su liste piccole impiegano troppo poco per avere un vantaggio usando async
    """
    def __init__ (self):
        self.timeout = 5.0
        self.active_list: List[str] = []
        self.all_list: List[str]= []
                
        self.name_file : str = settings.REGISTRY_FILE_NAME
        self.data_dir = Path(settings.REGISTRY_BASE_PATH)
        self.data_dir.mkdir(parents=True, exist_ok=True)#se esiste non solleva eccezioni, se no la crea
        self.complete_path = self.data_dir / self.name_file
        self.all_list= self._list_load()

        logger.info(f"📁 Path assoluto file registry: {self.complete_path.resolve()}")
        logger.info(f"📂 Directory corrente: {Path.cwd()}")

        

    async def update_active_list(self) -> List[str]:
        try:
            await self.check_avaibility()
            return self.active_list
        except Exception as e: 
            raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")
    

    def get_active_list(self)->List[str]:
        try:
            return self.active_list
        except Exception as e: 
            raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")
    
    def get_all_list(self)->List[str]:
        try:
            return self.all_list
        except Exception as e: 
            raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")
        


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



    def update_address_list(self, address: str):
        try:
            normalized_address = address.rstrip('/')
            if len(normalized_address)>2048:
                logger.warning(f"Max URL lenght permitted: 2048, the given URL lenght is:{len(normalized_address)}")
                raise HTTPException(status_code=400, detail=f"URL too long: {len(normalized_address)}")

            if normalized_address not in self.all_list:
                self.all_list.append(normalized_address)
                self._save_addresses()
                
                logger.info(f"Aggiunto nuovo indirizzo: {normalized_address}")
                

                return {
                    "status": "updated",
                    "address": normalized_address,
                    "total_addresses": len(self.all_list)
                }
            else:
                logger.info(f"Indirizzo già presente: {normalized_address}")
                return {
                    "status": "already_present",
                    "address": normalized_address,
                    "total_addresses": len(self.all_list)
                }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Errore durante l'aggiornamento: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")
        

    def _list_load(self)-> List[str]:
        try:
            if self.complete_path.exists():
                with open(self.complete_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"loaded {len(data)} addresses from memory")
                    return data
            else:
                logger.info("Adresses file not found")
                self._save_addresses([])  # Crea file vuoto
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Parsing error of registry file: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during the load of addresses file: {e}")
            return []



    def _save_addresses(self, addresses: List[str] = None):
        """Salva la lista degli indirizzi con atomic write"""
        if addresses is None:
            addresses = self.all_list
            
        try:
            # Scrittura atomica: scrivi su file temporaneo poi rinomina
            temp_file = self.complete_path.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(addresses, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Forza scrittura su disco
            
            # Rename atomico (su Linux/Unix è atomico)
            temp_file.replace(self.complete_path)
            
            logger.info(f"Salvate {len(addresses)} addresses sul file {self.complete_path}")
            
        except Exception as e:
            logger.error(f"Errore nel salvataggio addresses: {e}")
            raise



    def delete_address(self, address: str):
        try:
            # Normalizza l'indirizzo
            normalized_address = address.rstrip('/')
            
            # Validazione lunghezza
            if len(normalized_address) > 2048:
                logger.warning(f"Max URL length permitted: 2048, the given URL length is: {len(normalized_address)}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"URL too long: {len(normalized_address)}"
                )
            
            # Verifica se l'indirizzo esiste
            if normalized_address not in self.all_list:
                logger.warning(f"Address not found: {normalized_address}")
                raise HTTPException(
                    status_code=404, 
                    detail=f"Address not found: {normalized_address}"
                )
            
            # Rimuovi dalla lista in memoria
            self.all_list.remove(normalized_address)
            
            # Rimuovi anche dalla active_list se presente
            if normalized_address in self.active_list:
                self.active_list.remove(normalized_address)
                logger.debug(f"Removed from active_list: {normalized_address}")
            
            # Salva su disco
            self._save_addresses()
            
            logger.info(f"Deleted address: {normalized_address}")
            
            return {
                "status": "deleted",
                "address": normalized_address,
                "total_addresses": len(self.all_list),
                "active_addresses": len(self.active_list)
            }
            
        except HTTPException:
            # Rilancia le HTTPException così come sono
            raise
        except Exception as e:
            logger.error(f"Error during deletion: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")



                


