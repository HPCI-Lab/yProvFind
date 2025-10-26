import json
import os
from datetime import datetime, timezone
from pathlib import Path
from dishka import Provider, provide, Scope
import logging
from typing import List
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class TimestampManager:
    def __init__ (self, file_path: str = "last_fetch.json"):
        # cartella dove si trova questo file .py
        base_dir = Path(__file__).resolve().parent
        self.file_path = base_dir / file_path
       
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def get_last_fetch(self, address: str) -> str:
        """Legge ultimo timestamp o None se prima volta"""
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    logger.notice(f"Ultimo fetch per {address} effettuato il: {data.get(address)}")
                    return data.get(address)
            return None
        except Exception:
            return None
    
    def update_last_fetch(self, address: str):
        """Salva timestamp corrente in formato ISO 8601"""
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            # 1. CARICA dati esistenti
            existing_data = {}
            if self.file_path.exists() and self.file_path.stat().st_size > 0:
                try:
                    with open(self.file_path, 'r') as f:
                        existing_data = json.load(f) #load fallisce se il file è vuoto
                except json.JSONDecodeError: #se il file è vuoto o corrotto ritorna un file vuoto
                    existing_data = {}
            
            # 2. AGGIORNA solo questo address
            existing_data[address] = timestamp
            
            # 3. SALVA tutto
            with open(self.file_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
            logger.notice(f"Timestamp aggiornato per {address}: {timestamp}")
        except Exception as e:
            # Log ma non fallire
            logger.error(f"Errore salvataggio timestamp: {e}")



    def get_all_last_fetch(self):
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                logger.info("last fetch data sucesfully retrived")
                return data
            else:
                raise HTTPException(status_code=404, detail="no last fetch file found") 
            
        except HTTPException:
            raise
        except Exception as e: 
            raise HTTPException(status_code=500, detail="error during the riding of fetch timestamp")
        
        
    def delete_all_last_fetch(self):
        try:
            if self.file_path.exists():
                with open(self.file_path, "w") as f:
                    json.dump({}, f) 
                logger.info("fetch data sucesfully deleted")
                return {"status":"completed"}
            else:
                raise HTTPException(status_code=404, detail="no last fetch file found") 
            
        except HTTPException:
            raise
        except Exception as e: 
            raise HTTPException(status_code=500, detail="error during the riding of fetch timestamp")
            
    

    def delete_address_last_fetch(self, address: str):
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r') as f:
                    data = json.load(f)

            if address in data:
                del address
                logger.info(f"sucesfully removed {address}")
                return {"status:": "completed",
                        "removed:": address}
            else:
                raise HTTPException(status_code=400, detail="address not in list, address removal impossible")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"internal error during the deletion of {address}")
        

            
    #def modify_address_timestamp(self, address:str):
        


        
    




class TimestamProvider(Provider):
    @provide(scope=Scope.APP)
    async def timestamp_ptovider(self) -> TimestampManager:
        return TimestampManager()