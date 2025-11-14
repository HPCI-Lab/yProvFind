import logging
from sentence_transformers import SentenceTransformer

from typing import Dict, List, Tuple
import asyncio
from settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        #non serve specificare il percorso, hugging face ricerca automaticamente tra le cartelle del progetto modelCache/all-MiniLM-L6-v2
        try:
            if settings.USE_LOCAL_EMBEDDER:
                self.model = SentenceTransformer(model_name, local_files_only=True)
                logger.info("Model loaded from local cache")
            else:
                # Prova prima locale (cache da download precedente)
                try:
                    self.model = SentenceTransformer(model_name, local_files_only=True)
                    logger.info("Model found in cache (offline mode)")
                except:
                    # Scarica se non in cache
                    logger.info(f"Downloading model {model_name}...")
                    self.model = SentenceTransformer(model_name, local_files_only=False)
                    logger.info("Model downloaded successfully")
        except Exception as e:
            logger.critical(f"Cannot initialize embedding model: {e}")
            raise
    async def add_embeddings_to_batch(self, documents: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Processa documenti e restituisce (successi, fallimenti).
        
        Returns:
            Tuple[List[Dict], List[Dict]]: (documenti arricchiti, documenti falliti con error info)
        """
        failed = []
        success = []
        
        # Fase 1: Combina campi e traccia documenti validi
        valid_items = []  # Lista di (index, doc, text)
        
        for idx, doc in enumerate(documents):
            try:
                text = self._combine_fields(doc)
                if text is None:
                    logger.warning(f"Document {idx} skipped: all fields empty or invalid")
                    failed.append({
                        "doc": doc,
                        "error": "empty fields",
                        "index": idx
                    })
                    continue
                
                valid_items.append((idx, doc, text))
                
            except Exception as e:
                logger.error(f"Error combining fields for document {idx}: {e}")
                failed.append({
                    "doc": doc,
                    "error": f"Field combination error: {str(e)}",
                    "index": idx
                })
        
        # Se non ci sono documenti validi, restituisci subito
        if not valid_items:
            logger.warning("No valid documents to process")
            return [], failed
        
        # Fase 2: Genera embeddings solo per documenti validi
        try:
            valid_texts = [text for _, _, text in valid_items]
            logger.debug(f"Generating embeddings for {len(valid_texts)} valid documents")
            
            embeddings = await asyncio.to_thread(
                self.model.encode,
                valid_texts,
                convert_to_tensor=False,
                normalize_embeddings=True
            )
            
        except Exception as e:
            logger.critical(f"Fatal error during embedding generation: {e}")
            # Tutti i documenti validi diventano falliti
            for idx, doc, _ in valid_items:
                failed.append({
                    "doc": doc,
                    "error": f"Embedding batch failed: {str(e)}",
                    "index": idx
                })
            return [], failed
        
        # Fase 3: Assegna embeddings ai documenti
        for (idx, doc, text), embedding in zip(valid_items, embeddings):
            try:
                # Validazione embedding
                if embedding is None or len(embedding) == 0:
                    raise ValueError("Empty embedding returned")
                
                enriched_doc = doc.copy()
                enriched_doc["_source"]["semantic_embedding"] = embedding.tolist()
                success.append(enriched_doc)
                
            except Exception as e:
                logger.error(f"Error assigning embedding to document {idx}: {e}")
                failed.append({
                    "doc": doc,
                    "error": f"Embedding assignment error: {str(e)}",
                    "index": idx
                })
        
        logger.info(
            f"Embedding batch completed: {len(success)} successes, "
            f"{len(failed)} failures out of {len(documents)} total documents"
        )
        
        return success, failed
    
    def _combine_fields(self, document: Dict) -> str | None:
        """
        Combina i campi rilevanti del documento in un'unica stringa.
        
        Returns:
            str | None: Testo combinato o None se tutti i campi sono vuoti
        """
        src = document.get('_source', {})
        
        # Estrai e pulisci campi
        title = (src.get('title') or '').strip()
        description = (src.get('description') or '').strip()
        author = (src.get('author') or '').strip()
        
        # Gestisci keywords (può essere stringa o lista)
        keywords = src.get('keywords') or []
        if isinstance(keywords, str):
            keywords = [keywords]
        elif not isinstance(keywords, list):
            keywords = []
        
        keywords_text = ', '.join([kw.strip() for kw in keywords if isinstance(kw, str) and kw.strip()])
        
        # Costruisci testo finale
        parts = []
        if title:
            parts.append(title)
        if description:
            parts.append(description)
        if keywords_text:
            parts.append(f"Keywords: {keywords_text}")
        if author:
            parts.append(f"Author: {author}")
        
        return '. '.join(parts) if parts else None
        

    async def _get_query_embedding(self, query: str) -> List[float]:
        """
        Converte la query dell'utente in embedding
        """
        try:
            # Usa lo stesso embedding service dell'indexing
            embedding = await asyncio.to_thread(
                self.model.encode,
                [query],
                convert_to_tensor=False,
                normalize_embeddings=True
            )
            return embedding[0].tolist()
            
        except Exception as e:
            logger.error(f"Errore nel calcolo embedding per query '{query}': {e}")
            raise

        