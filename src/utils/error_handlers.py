import asyncio
import traceback
import logging
from fastapi import HTTPException
from elasticsearch import RequestError, TransportError, NotFoundError, ConnectionError

logger = logging.getLogger(__name__)

async def safe_es_call(coro, operation_type: str = "search", timeout: int = 30):
    """
    Esegue una coroutine Elasticsearch e gestisce gli eventuali errori

    operation_type: "search" | "delete" | "update" | "admin"
    timeout: timeout in secondi (solo per search o operazioni lunghe)
    
    """
    try:
        if operation_type in ["search", "update"]:
            return await asyncio.wait_for(coro, timeout=timeout)
        else:
            return await coro

    except asyncio.TimeoutError:
        logger.error(f"Timeout ({timeout}s) during Elasticsearch {operation_type}")
        raise HTTPException(status_code=504, detail=f"{operation_type.capitalize()} operation timed out")

    except NotFoundError as e:
        logger.warning(f"{operation_type.capitalize()} target not found: {e.info if hasattr(e, 'info') else e}")
        raise HTTPException(status_code=404, detail=f"{operation_type.capitalize()} target not found")

    except ConnectionError as e:
        logger.error(f"Elasticsearch connection error during {operation_type}: {e}")
        raise HTTPException(status_code=503, detail="Elasticsearch connection error")

    except RequestError as e:
        logger.error(f"Invalid request to Elasticsearch during {operation_type}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid {operation_type} request or mapping mismatch")

    except TransportError as e:
        logger.error(f"Elasticsearch transport error during {operation_type}: {e}")
        raise HTTPException(status_code=502, detail=f"Elasticsearch transport error during {operation_type}")

    except Exception as e:
        logger.error(f"Unexpected error during {operation_type}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Unexpected internal error during {operation_type}")
