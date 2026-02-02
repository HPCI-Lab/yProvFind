from .prov_analyzer import ProvAnalyzer
from typing import List, Dict, AsyncIterator
import httpx
import asyncio
from logging import getLogger
from dishka import Provider, provide, Scope
from services.LLM.llm import LLMModel
from services.LLM.llm import Gemini
from services.LLM.llm import Groq
import re 
SEMAPHORE:int = 5

logger = getLogger(__name__)





prompt="""Role: Expert Semantic Forensic Analyst. Task: You are tasked with reconstructing the complex narrative behind technical provenance records. You must transform raw metadata traces into a professional executive summary that explains the "why" and "how" of the recorded operations.

Output Structure (Mandatory): Description: [A paragraph of exactly 5 lines] Keywords: [10 distinct, domain-specific keywords]

Analysis Methodology:

    Identify the Core Logic: Look at the relationship between names (e.g., file names, user tags) and resource metrics (CPU, Memory, IO, Network).

    Determine the Domain: Is this a software build, a scientific simulation, a data pipeline, or a hardware stress test?

    Infer the Impact: What does the presence of specific sensors (like gpu_temperature or disk_usage) imply about the intensity or the goal of the task?

Strict Requirements:

    Description Length: You MUST write exactly 5 lines. If the information is sparse, elaborate on the technical implications, the necessity of the monitored metrics for auditability, and the likely professional context of the observer (the agent).

    Semantic Depth: Do NOT summarize the file structure. Describe the event that the file represents. Use active verbs and technical terminology appropriate for the inferred domain.

    Negative Constraints: Do NOT use: "entity", "activity", "agent", "count", "JSON", "contains", "provides". Do NOT mention the file name or data types.

    Keyword Quality: Provide exactly 10 keywords. Avoid generic words like "data" or "process". Use compound technical terms (e.g., "Resource Saturation Analysis", "Deterministic Workflow Tracking").

Input Text: 
"""







class MetaEnricher:
    def __init__(self, analyzer: ProvAnalyzer, llm: Groq):
        self.analyzer=analyzer
        self.llm = llm
        self.client=httpx.AsyncClient()
        self.semaphore=asyncio.Semaphore(SEMAPHORE)
    
    async def _download_doc(self, doc: Dict):
        link=doc["_source"].get("storage_url")
        if not link:
            return None
        
        async with self.semaphore:
            try: 
                raw_doc=await self.client.get(link)
                raw_doc.raise_for_status()
                return raw_doc.json()
            except httpx.HTTPStatusError as e:
                logger.warning(f"Enricher: download of document {doc.get("_id")} failed: {e}")
                raise
            except ValueError: 
                logger.error("The downloaded file is not a provenace in json format")
                raise

    

    def _run_analyzer(self, provenance_list:List[Dict])->List[str]:

        analyzed_list=[]

        for prov in provenance_list:

            if isinstance (prov, Exception):
                analyzed_list.append(prov)
                continue

            try:
                #analysis file 
                analyzed_prov=self.analyzer.generate_simple_llm_context(prov)
                analyzed_prov+=self.analyzer.debug_data_structure(prov)
                analyzed_list.append(analyzed_prov)
            except Exception as e:
                logger.error(f"Provenance {prov.get('_id')} analysis failed")
                analyzed_list.append(e)

        return analyzed_list
        


    async def llm_call(self, analyzed, metadata):
        """Execute LLM call only if input is not an exception."""
        async with self.semaphore:
            #if the file is an error return the error in the list
            if isinstance (analyzed, Exception):
                return analyzed
            
            meta_description=""
            if metadata.get("_source") and metadata["_source"].get("description"):
                meta_description = f" \n Provenance file description: {metadata['_source']['description']} \n"
       



            complete_prompt=prompt + meta_description + analyzed

        
            try:
                response = await self.llm.chat(complete_prompt)
                return response
            except Exception as e:
                logger.error(f"LLM keywords generation failed: {e}")
                return Exception(f"LLM keywords generation failed: {str(e)}")
            


                

    async def meta_enricher(self, metadata: List[Dict]):
        failed:List[Dict]=[]
        #download file di provenance
        try:
            logger.info("Enricher: start the provenace file download...")
            download_task=[self._download_doc(doc) for doc in metadata]
            prov_list=await asyncio.gather(*download_task, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Enricher: provenace file download failed: {e}")
            return metadata, [{"doc": m.get("_id"), "error": str(e)} for m in metadata]

        #analisi dei file di provenace
        try:
            logger.info("Enricher: Start the analyzer...")
            analyzed_list = await asyncio.to_thread(self._run_analyzer, prov_list)
            
        except Exception as e:
            logger.error(f"Enricher: analyzer error: {e}")
            return metadata, [{"doc": m.get("_id"), "error": str(e)} for m in metadata]
        #generazione di descrizione e keywords
        try:
            logger.info("Enricher: Calling LLM to generate keywords and description...")
            llm_task=[self.llm_call(doc, meta) for doc, meta in zip(analyzed_list, metadata)]
            llm_processed_list= await asyncio.gather(*llm_task, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Enricher: llm failed to create description and keywords:{e}")
            return metadata, [{"doc": m.get("_id"), "error":  str(e)} for m in metadata]
        #unione delle generazioni della llm con la lista originale
        logger.info("Enricher: Merging metadata with LLM generations...")
        for meta, processed in zip(metadata, llm_processed_list):
            if isinstance(processed, Exception):
                failed.append({
                    "doc":meta.get("_id"),
                    "error":str(processed)
                })
                continue
            
            # Estrazione Descrizione
            # Cerchiamo il testo tra 'description:' e 'keywords:'
            desc_match = re.search(r"description:\s*(.*?)\s*(?=keywords:|$)", processed, re.IGNORECASE | re.DOTALL)
            description_text = desc_match.group(1).strip() if desc_match else processed.strip()

            # Estrazione Keywords
            # Cerchiamo tutto ciò che segue 'keywords:'
            key_match = re.search(r"keywords:\s*(.*)", processed, re.IGNORECASE | re.DOTALL)
            
            keywords_list = []
            if key_match:
                raw_keywords = key_match.group(1)
                # Pulizia: dividiamo per virgola, togliamo spazi e scartiamo stringhe vuote
                keywords_list = [k.strip() for k in raw_keywords.split(",") if k.strip()]
            #Assegnazione ai metadati originali
            meta["_source"]["llm_description"] = description_text


            if meta["_source"]["keywords"] is None:
                meta["_source"]["keywords"] = []
            meta["_source"]["keywords"].extend(keywords_list)


            
        return metadata, failed




        
        







    async def close(self):
        await self.client.aclose()

    



            


        












        

        