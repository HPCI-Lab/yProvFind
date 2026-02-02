from dishka import Scope, Provider, provide
from .llm import LLMModel
from .llm import Gemini
from .llm import Groq
class LLMProvider(Provider):

    @provide(scope=Scope.APP)
    def llm_provider(self)->LLMModel:
        return LLMModel()
    
    @provide(scope=Scope.APP)
    def llm_provider_gemini(self)->Gemini:
        return Gemini()

    @provide(scope=Scope.APP)
    def llm_provider_gemini(self)->Groq:
        return Groq()

