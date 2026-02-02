from .meta_enricher import MetaEnricher
from .prov_analyzer import ProvAnalyzer
from services.LLM.llm import Groq
from typing import AsyncIterator
from dishka import provide, Scope, Provider
#from services.LLM.llm import OpenRouter
#from services.LLM.llm import Gemini


class MetaEnricherProvider(Provider):
    @provide(scope=Scope.APP)
    async def enricher_provider(self, analyzer: ProvAnalyzer, llm: Groq)->AsyncIterator[MetaEnricher]:
        meta_enricher=MetaEnricher(analyzer, llm)
        try:
            yield meta_enricher
        finally:
            await meta_enricher.close()

            
        