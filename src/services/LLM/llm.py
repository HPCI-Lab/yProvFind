from settings import settings
from logging import getLogger
logger = getLogger(__name__)
import litellm



class LlmHandler:
    def __init__(self, provider:str=None, model:str=None, key:str=None):
        """start with an empty istance of llm, the user must select the provider and the model"""
        self.provider=provider
        self.model=model
        self.key=key

    def update_config_llm(self,provider,model,key):
        """Method for updating configuration and key on the fly without recreating the class"""
        self.provider=provider
        self.model=model
        self.key=key

    def key_and_model_check(self) -> bool:
        return all([self.provider, self.key, self.model])

    async def check_if_the_model_is_active(self, timeout: float = 10.0) -> bool:
        try:
            await litellm.acompletion(
                model=f"{self.provider}/{self.model}",
                messages=[{"role": "user", "content": "hi"}],
                api_key=self.key,
                max_tokens=100,
                timeout=timeout,
            )
            return True
        except Exception as exc:
            logger.error(
                "The model is not responding; please verify that the key and the data "
                f"provided for the model calls are correct. Error: {type(exc).__name__}"
            )
            return False
        

    async def chat(self, prompt):
        if not self.provider or not self.key or not self.model:
            raise ValueError("The service APIs or the model have not been set.")

        response = litellm.completion(
            model=f"{self.provider}/{self.model}",
            messages=[{"role": "user", "content": prompt}],
            api_key=self.key
        )
        return response.choices[0].message.content



"""
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