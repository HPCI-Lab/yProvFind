from dishka import Scope, Provider, provide
from .llm import LlmHandler
#from .llm import OpenRouter
#from .llm import Gemini


class LLMProvider(Provider):
    @provide(scope=Scope.APP)
    def llm_provider_groq(self)->LlmHandler:
        return LlmHandler()
    
    """
    @provide(scope=Scope.APP)
    def llm_provider(self)->OpenRouter:
        return OpenRouter()
    
    @provide(scope=Scope.APP)
    def llm_provider_gemini(self)->Gemini:
        return Gemini()
    """


