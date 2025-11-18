from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.embedding.embedder import EmbeddingService
from services.indexer.indexer import IndexService
import json
import logging
from fastapi import HTTPException
from dishka import Provider, provide, Scope
from pathlib import Path
from settings import settings
logger = logging.getLogger(__name__)


class Demo:
    def __init__(self,es_conn: ElasticSearchConnection, embedder: EmbeddingService, indexer: IndexService ):
        self.es_conn = es_conn
        self.embedder = embedder
        self.indexer = indexer
        

    async def start_demo(self):
        es_total_success = 0
        es_total_errors = []
        # percorso della cartella in cui si trova questo file
        BASE_DIR = Path(__file__).resolve().parent
        
        # percorso del JSON
        json_path = BASE_DIR / "example_documents" / "documents_list.json"
        
        try: 
            with open(json_path, "r", encoding="utf-8") as f:
                documents = json.load(f)
        except FileNotFoundError as e:
            logger.error(f"Sample documents file not found: {e}")
            raise HTTPException(
                status_code=404, 
                detail="Demo configuration error: sample documents file not found"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in sample documents: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Demo configuration error: invalid sample documents format"
            )
        except Exception as e:
            logger.error(f"Unexpected error reading sample documents: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to load demo documents"
            )
        
        
        try:
            enriched_list, embedding_failures = await self.embedder.add_embeddings_to_batch(documents)
            
            es_success, es_errors = await self.indexer.index_enriched_batch(enriched_list)
            es_total_success += es_success
            es_total_errors.extend(es_errors)
        except Exception as e: 
            logger.error(f"Start demo failed during indexing: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to index demo documents"
            )
        
        
        if es_total_errors:
            logger.warning(f"Demo started with {len(es_total_errors)} indexing errors")
            return {
                "status": "Demo started with warnings",
                "indexed": es_total_success,
                "errors": len(es_total_errors)
            }
        
        return {
            "status": "Demo started successfully",
            "indexed": es_total_success
        }
    

    async def end_demo(self):
        BASE_DIR = Path(__file__).resolve().parent
        
        # percorso del JSON
        json_path = BASE_DIR / "example_documents" / "documents_list.json"
        
        try: 
            with open(json_path, "r", encoding="utf-8") as f:
                documents = json.load(f)
        except FileNotFoundError as e:
            logger.error(f"Sample documents file not found: {e}")
            raise HTTPException(
                status_code=404, 
                detail="Demo configuration error: sample documents file not found"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in sample documents: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Demo configuration error: invalid sample documents format"
            )
        except Exception as e:
            logger.error(f"Unexpected error reading sample documents: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to load demo documents"
            )
        

        try:    
            document_list=[]
            for doc in documents:
                pid = doc.get("_id")
                document_list.append({"delete":{"_index": "documents" , "_id": pid}})

            response= await self.es_conn.client.bulk(operations=document_list)

            if response['errors']:
                errored_documents = []
                for i, item in enumerate(response['items']):
                    operation = list(item.keys())[0]
                    if 'error' in item[operation]:
                        errored_documents.append({
                            'id': documents.get(i),
                            'status': item[operation]['status'],
                            'error': item[operation]['error']
                        })
                logger.error(f"error while deleting: {errored_documents}")
                raise HTTPException(status_code=500, detail="error while deleting demo documents")
            
            return {"status" : "Demo ended succesfully"}

                
        except Exception as e:
            logger.error(f"demo deactivation failed, some documents are still in memory: {e}")

        


class DemoProvider(Provider):
    @provide(scope= Scope.REQUEST)
    def demo_prvider(self ,es_conn:ElasticSearchConnection, embedder: EmbeddingService, indexer: IndexService)-> Demo:
        return Demo(es_conn, embedder, indexer)