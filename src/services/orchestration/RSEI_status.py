from datetime import datetime
from typing import Optional
import asyncio


class RSEIStatus:
    def __init__(self):
        # Initialize all attributes with default values
        self._status: str = "idle"
        self._details: str = ""
        self._ES_successfully_indexed: int = 0  # ← Fixed: int not str
        self._ES_error_count: int = 0  # ← Fixed: int not str
        self._embed_success: int = 0  # ← Fixed: int not str
        self._embed_error: int = 0  # ← Fixed: int not str
        self._started_at: Optional[str] = None
        self._completed_at: Optional[str] = None
        self._lock = asyncio.Lock()  # ← CRITICAL: This was missing!

    @property
    def status(self) -> str:
        return self._status  # ← Fixed: was returning self.status (infinite recursion!)

    @property
    def details(self) -> str:
        return self._details
    
    @property
    def ES_successfully_indexed(self) -> int:  # ← Fixed: return type int not str
        return self._ES_successfully_indexed
    
    @property
    def ES_error_count(self) -> int:  # ← Fixed: return type int not str
        return self._ES_error_count

    @property
    def embed_success(self) -> int:  # ← Fixed: return type int not str
        return self._embed_success
    
    @property
    def embed_error(self) -> int:  # ← Fixed: return type int not str
        return self._embed_error
    
    @property
    def started_at(self) -> Optional[str]:
        return self._started_at
    
    @property
    def completed_at(self) -> Optional[str]:
        return self._completed_at
    
        
    # Status check methods
    def is_running(self) -> bool:
        return self._status == "running"
    
    def is_idle(self) -> bool:
        return self._status == "idle"
    
    async def start_process(self):
        """Mark process as started"""
        async with self._lock:
            self._status = "running"
            self._details = "Initialization..."
            self._started_at = datetime.now().isoformat()
            self._completed_at = None

    async def update_details(self, details: str):
        """Update process details"""
        async with self._lock:
            self._details = details
    
    async def update_counters(
        self,
        es_indexed: int,
        es_errors: int,
        embed_success: int,
        embed_errors: int
    ):
        """Update all counters"""
        async with self._lock:
            self._ES_successfully_indexed = es_indexed
            self._ES_error_count = es_errors
            self._embed_success = embed_success
            self._embed_error = embed_errors
    
    async def complete_process(
        self,
        es_indexed: int,
        es_errors: int,
        embed_success: int,
        embed_errors: int,
        details: str = "Process completed successfully"
    ):
        """Mark process as completed"""
        async with self._lock:
            self._status = "completed"
            self._details = details
            self._ES_successfully_indexed = es_indexed
            self._ES_error_count = es_errors
            self._embed_success = embed_success
            self._embed_error = embed_errors
            self._completed_at = datetime.now().isoformat()
    
    async def interrupt_process(self, reason: str):
        """Mark process as interrupted"""
        async with self._lock:
            self._status = "interrupted"
            self._details = reason
            self._completed_at = datetime.now().isoformat()
    
    async def error_process(
        self,
        error_message: str,
        es_indexed: int,
        es_errors: int,
        embed_success: int,
        embed_errors: int
    ):
        """Mark process as failed"""
        async with self._lock:
            self._status = "error"
            self._details = error_message
            self._ES_successfully_indexed = es_indexed
            self._ES_error_count = es_errors
            self._embed_success = embed_success
            self._embed_error = embed_errors
            self._completed_at = datetime.now().isoformat()
    
    async def reset(self):
        """Reset status to idle"""
        async with self._lock:
            self._status = "idle"
            self._details = ""
            self._ES_successfully_indexed = 0
            self._ES_error_count = 0
            self._embed_success = 0
            self._embed_error = 0
            self._started_at = None
            self._completed_at = None
    
    def to_dict(self) -> dict:
        """Export status as dictionary"""
        return {
            "status": self._status,
            "details": self._details,
            "ES_successfully_indexed": self._ES_successfully_indexed,
            "ES_error_count": self._ES_error_count,
            "embed_success": self._embed_success,
            "embed_error": self._embed_error,
            "started_at": self._started_at,
            "completed_at": self._completed_at
        }