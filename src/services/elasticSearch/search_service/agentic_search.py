import json
import logging
import httpx
from typing import Dict, List, Any, Optional
from ..connection.es_connection import ElasticSearchConnection
from .full_text_search import FullTextSearch
from settings import settings

logger = logging.getLogger(__name__)

class AgenticSearch:
    def __init__(self, es_conn: ElasticSearchConnection):
        self.es_conn = es_conn
        # Instantiate your existing FullTextSearch class to reuse its query building & formatting logic
        self.ftx_search = FullTextSearch(es_conn)
        # Point to your local Ollama instance (typically running on host or sidecar container)
        self.ollama_url = getattr(settings, "OLLAMA_URL", "http://ollama:11434/api/chat")
        self.model_name = getattr(settings, "OLLAMA_MODEL", "qwen3.5:0.8b")

    async def search(self, user_prompt: str, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Main entry point. Uses a local Ollama model to orchestrate tool extraction,
        executes an exact database search based on the extracted values, and synthesizes 
        the ultimate answer.
        """
        logger.info(f"Starting agentic search for prompt: {user_prompt}")
        
        # 1. Ask Ollama to act as a router/parameter extractor using JSON Mode
        try:
            tool_call_params = await self._get_tool_parameters(user_prompt)
            logger.debug(f"Agent extracted parameters: {tool_call_params}")
        except Exception as e:
            logger.error(f"Failed parsing tool arguments with Ollama: {str(e)}")
            # Fallback gracefully to basic full-text querying if LLM structuring fails
            tool_call_params = {"query": user_prompt, "filters": {}, "page_size": 5, "include_all_versions": False}

        # 2. Execute the underlying Elasticsearch tool with the structured parameters
        raw_db_results = await self.ftx_search.search(
            query=tool_call_params.get("query", user_prompt),
            addFilters=tool_call_params.get("filters", {}),
            page_size=tool_call_params.get("page_size", 10),
            include_all_versions=tool_call_params.get("include_all_versions", False),
            timeout=timeout
        )

        if not raw_db_results:
            return {
                "agent_response": "I searched the provenance database but found no records matching your request.",
                "raw_results": []
            }

        # 3. Feed the database hits back into Ollama to formulate a natural answer
        agent_final_answer = await self._synthesize_final_response(user_prompt, raw_db_results)

        return {
            "agent_response": agent_final_answer,
            "raw_results": raw_db_results
        }

    async def _get_tool_parameters(self, user_prompt: str) -> Dict[str, Any]:
        """
        Uses Ollama's JSON mode to force structured data extraction out of natural user language.
        """
        system_instruction = (
            "You are an AI data router. Your job is to extract search parameters from a user prompt. "
            "You MUST reply with a single JSON object matching this schema exactly:\n"
            "{\n"
            '  "query": "the optimized text keyword to look up",\n'
            '  "filters": {\n'
            '    "date_from": "DD-MM-YYYY or null",\n'
            '    "date_to": "DD-MM-YYYY or null",\n'
            '    "version": integer or null,\n'
            '    "yProvIstance": "url string or null"\n'
            "  },\n"
            '  "page_size": integer default 10,\n'
            '  "include_all_versions": boolean default false\n'
            "}\n"
            "Do not add markdown formatting wrappers or conversational commentary."
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Extract parameters for: {user_prompt}"}
            ],
            "options": {
                "num_predict": 150,
                "temperature": 0.0,
                "top_p": 0.1
            },
            "stream": False,
            "format": "json"  # Forces Ollama to output valid structural JSON
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.ollama_url, json=payload, timeout=15.0)
            if response.status_code != 200:
                raise Exception(f"Ollama returned status code {response.status_code}")
            
            result_json = response.json()
            content_str = result_json.get("message", {}).get("content", "{}")
            return json.loads(content_str)

    async def _synthesize_final_response(self, user_prompt: str, db_results: List[Dict[str, Any]]) -> str:
        """
        Passes the extracted database data array back to Ollama to summarize the results.
        """
        # Clean up database source fields slightly to keep context windows lighter
        cleaned_docs = []
        for doc in db_results:
            source = doc.get("source", {})
            cleaned_docs.append({
                "id": doc.get("id"),
                "score": doc.get("score"),
                "title": source.get("title"),
                "description": source.get("description"),
                "version": source.get("version"),
                "author": source.get("author"),
                "pid": source.get("pid")
            })

        system_instruction = (
            "You are an expert assistant managing provenance data tracking. "
            "Analyze the given raw database records and provide a concise, grounded, "
            "and factual answer summarizing what was found. Rely ONLY on the provided records. "
            "If version metadata or lineage tracking is relevant, emphasize it."
        )

        user_content = (
            f"User Original Query: {user_prompt}\n\n"
            f"Retrieved Provenance Documents:\n{json.dumps(cleaned_docs, indent=2)}"
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            "options": {
                "temperature": 0.3
            },
            "stream": False
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.ollama_url, json=payload, timeout=None)
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "Error compiling response.")
            return f"Error connecting to Ollama generation module (HTTP {response.status_code})."