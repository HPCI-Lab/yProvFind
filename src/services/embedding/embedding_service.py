import logging
from sentence_transformers import SentenceTransformer
from services.fetch_and_index.fetcher import DocumentFetcher

from typing import Dict, List
import asyncio

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model= SentenceTransformer(model_name, local_files_only=True)
        logger.debug(f"Used model: {self.model}")
        logger.debug("The model is loaded from the local cache")

    async def add_embeddings_to_batch(self, documents: List[Dict]) -> List[Dict]:
        
        try: 
            texts = await asyncio.gather(*[self._combine_fields(doc) for doc in documents])
            logger.debug(f"Calcolo embeddings per {len(texts)} documenti")

            embeddings = await asyncio.to_thread(
                self.model.encode, 
                texts,
                convert_to_tensor=False,  # Vogliamo liste Python, non tensori
                normalize_embeddings=True  # Normalizza per cosine similarity
            )


            enriched_documents= []
            for doc, embedding in zip(documents, embeddings):
                enriched_doc= doc.copy()
                enriched_doc['_source']['semantic_embedding']=embedding.tolist()
                enriched_documents.append(enriched_doc)

            logger.debug(f"Embeddings calcolati con successo per {len(enriched_documents)} documenti")
            return enriched_documents
               

        except Exception as e:
            logger.error(f"error during the embeddings:{e}")
            raise



    async def _combine_fields(self, document: Dict)-> str:
        """
        Combina title e description per creare il testo da embeddare
        
        Args:
            document: Documento con campi title, description, etc.
            
        Returns:
            Testo combinato pronto per l'embedding
        """
        title = document.get('_source', {}).get('title', '').strip()
        description = document.get('_source', {}).get('description', '').strip()
        if title and description:
            return f"{title}. {title}. {description}"
        elif title:
            return title
        elif description:
            return description
        else:
            # Fallback se non c'è contenuto
            return "No content available"
        

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

        