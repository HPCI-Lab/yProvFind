import json
import os
from datetime import datetime, timezone
from pathlib import Path
from dishka import Provider, provide, Scope
import logging
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class TimestampManager:
    def __init__ (self, file_path: str = "last_fetch.json"):
        # cartella dove si trova questo file .py
        base_dir = Path(__file__).resolve().parent
        self.file_path = base_dir / file_path
        # crea la cartella se non esiste
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    async def get_last_fetch(self, address: str) -> str:
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
    
    async def update_last_fetch(self, address: str):
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


class TimestamProvider(Provider):
    @provide(scope=Scope.APP)
    async def timestamp_ptovider(self) -> TimestampManager:
        return TimestampManager()