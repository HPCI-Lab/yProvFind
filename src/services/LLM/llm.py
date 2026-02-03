from settings import settings
import asyncio
from logging import getLogger
import httpx
logger = getLogger(__name__)




from groq import AsyncGroq
class Groq:
    def __init__(self):
        

        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        logger.info(f"Groq Client inizializzato. Key presente: {bool(settings.GROQ_API_KEY)}")

    async def chat(self, prompt: str):
        try:
            completion = await self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ], 
            )

            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM: failed to contact the llm: {e}")
            raise

"""
from openai import OpenAI, AsyncOpenAI
class OpenRouter:
    def __init__(self):
        self.client= AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=settings.OPEN_ROUTER,
                    timeout=60.0,
                    default_headers={
                                    "HTTP-Referer": "http://localhost",   
                                    "X-Title": "provenance-tool",         
                                    }
                    )

    async def chat(self, prompt:str):
        response = await self.client.chat.completions.create(
                                            model="nousresearch/hermes-3-llama-3.1-405b:free",
                                            messages=[{ "role": "user", "content": prompt}]
                                        )

        return response.choices[0].message.content
    


from google import genai

class Gemini:
    def __init__(self):

        self.client=genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model= "gemini-2.5-flash"

    async def chat(self, prompt: str):
        def call():
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            return client.models.generate_content(
                model=self.model,
                contents=prompt
            )

        response = await asyncio.to_thread(call)
        return response.text
"""