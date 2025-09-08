from .elasticSearch.es_provider import ElasticSearchService
from .document_fetcher.provider import DocumentFetcherProvider

__all__ = ("providers",)

providers =[ElasticSearchService,
            DocumentFetcherProvider]
