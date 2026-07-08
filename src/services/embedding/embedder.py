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
                    
            self.max_token_number = self.model.get_max_seq_length()
            logger.info(f"Max token number for the embedding model {model_name}: {self.max_token_number}")
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
                    logger.warning(f"Embedder: document {doc.get("_id")} skipped: all fields empty or invalid")
                    failed.append({
                        "doc": doc.get("_id"),
                        "error": "Embedder: empty fields, creating an embedding is impossible"
                    })
                    continue
                
                #verifica che il documento non contenga piu token di quelli che porcessa il modello di embedding
                token=self.model.tokenizer(text)
                num_token=len(token["input_ids"])
                if  num_token > self.max_token_number:
                    logger.warning(f"The number of tokens in the document exceeds the maximum number of " \
                    f"tokens that the embedding template can process. Only the first {self.max_token_number} tokens in the document " \
                    f"will be embedding. \nNumber of token in the file: {num_token} \nNumber of tokens that will be discard:{num_token-self.max_token_number}")

                
                valid_items.append((idx, doc, text))
                
            except Exception as e:
                logger.error(f"Error combining fields for document {idx}: {e}")
                failed.append({
                    "doc": doc.get("_id"),
                    "error": f"Field combination error: {str(e)}",
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
                    "doc": doc.get("_id"),
                    "error": f"Embedding entire batch failed: {str(e)}",
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
                    "doc": doc.get("_id"),
                    "error": f"Embedding assignment error: {str(e)}",
                })
        
        logger.info(
            f"Embedding batch completed: {len(success)} successes, "
            f"{len(failed)} failures out of {len(documents)} total documents"
        )
        
        return success, failed
    
    def _combine_fields(self, document: Dict) -> str | None:
        """
        Combina la struttura PROV-JSON complessa di un esperimento ML 
        in una stringa descrittiva ottimizzata per modelli di embedding.
        """
        src = document.get('_source', {})
        
        # Se il documento è racchiuso dentro un classico dizionario Elasticsearch, estrailo,
        # altrimenti leggi direttamente la radice se viene indicizzato il file raw.
        data = src if any(k in src for k in ['activity', 'entity', 'agent']) else document

        parts = []

        # 1. Estrazione Attività Principale ed Esperimento (Hardware, OS, Runtime)
        activities = data.get('activity', {})
        for act_name, act_meta in activities.items():
            # Identifichiamo il blocco principale dell'esperimento (es. "example_GR0_2")
            if 'yprov:experiment_name' in act_meta:
                exp_name = act_meta.get('yprov:experiment_name')
                py_version = act_meta.get('yprov:python_version', '').split('|')[0].strip()
                os_system = act_meta.get('yprov:operating_system', '')
                proc = act_meta.get('yprov:processor', '')
                
                parts.append(f"Machine Learning Experiment Name: {exp_name}")
                if py_version:
                    parts.append(f"Environment: Running Python {py_version} on {os_system} {proc} hardware Architecture")

        # 2. Estrazione Iperparametri Globali ed Entità (Modelli, Dataset, Configurazione)
        entities = data.get('entity', {})
        hyperparams = []
        datasets_info = []
        metrics_summary = []

        for ent_name, ent_meta in entities.items():
            label = ent_meta.get('prov:label', ent_name)
            value = ent_meta.get('prov:value')
            prov_type = ent_meta.get('prov:type', '')

            # Raccogli gli iperparametri (es. optimizer, loss, epochs, learning_rate, device)
            if value and ent_name in ['optimizer', 'loss', 'batch_size', 'epochs', 'learning_rate', 'device']:
                hyperparams.append(f"{label}: {value}")
            
            # Identifica e descrivi i Dataset (Train, Validation, Test)
            elif 'provml:Dataset' in prov_type:
                role = ent_meta.get('prov:role', 'dataset')
                total_samples = ent_meta.get('yprov:train_dataset_stat_total_samples') or \
                                ent_meta.get('yprov:val_dataset_stat_total_samples') or \
                                ent_meta.get('yprov:test_dataset_stat_total_samples')
                if total_samples:
                    # Estrae il numero pulito rimuovendo l'involucro xsd se presente
                    if isinstance(total_samples, dict) and '$' in total_samples:
                        total_samples = total_samples['$']
                    datasets_info.append(f"{label} ({role}) with {total_samples} total samples")

            # Identifica il Modello Generato ed i suoi Parametri hardware/memoria
            elif 'provml:Model' in prov_type:
                identifier = ent_meta.get('dcterms:identifier', 'Model checkpoint')
                params_key = [k for k in ent_meta.keys() if 'total_params' in k]
                
                model_str = f"Output Model Architecture: saved as {identifier}"
                if params_key:
                    p_val = ent_meta[params_key[0]]
                    p_num = p_val.get('$') if isinstance(p_val, dict) else p_val
                    model_str += f" containing {p_num} weights parameters"
                parts.append(model_str)

            # Estrazione Statistiche dei Metric Node (Accuracy, MSE Loss per Training/Validazione)
            elif 'provml:Metric' in prov_type:
                context = ent_meta.get('yprov:context', '')
                identifier = ent_meta.get('dcterms:identifier')
                
                # Se l'identificatore è un dizionario riassuntivo (contiene mean, std, min, max)
                if isinstance(identifier, dict) and 'mean' in identifier:
                    mean_val = identifier.get('mean')
                    metrics_summary.append(f"{label} in context {context} reached a mean score value of {mean_val:.6f}")

        # Inietta le liste raggruppate all'interno delle stringhe finali del prompt semantico
        if hyperparams:
            parts.append(f"Training Hyperparameters configuration: {', '.join(hyperparams)}")
        if datasets_info:
            parts.append(f"Datasets utilized: {'; '.join(datasets_info)}")
        if metrics_summary:
            parts.append(f"Performance Metrics Summary: {'. '.join(metrics_summary)}")

        # 3. Estrazione dell'autore (Agent)
        agents = list(data.get('agent', {}).keys())
        if agents:
            parts.append(f"Executed and Authored by scientist agent: {', '.join(agents)}")

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

        