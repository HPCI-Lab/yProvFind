from .elasticSearch.es_provider import ElasticSearchService
from .document_fetcher.provider import DocumentFetcherProvider, BulkIndexerProvider
from .elasticSearch.es_provider import Multi_match_search_provider
__all__ = ("providers",)

providers =[ElasticSearchService,
            DocumentFetcherProvider,
            BulkIndexerProvider,
            Multi_match_search_provider]
