from dishka import Provider, provide, Scope
from .embedder import EmbeddingService


class EmbeddingProvider(Provider):
    @provide(scope=Scope.APP)  # Singleton - il modello è pesante da caricare
    def get_embedding_service(self) -> EmbeddingService:
        return EmbeddingService(model_name="all-MiniLM-L6-v2")