from .elasticSearch.connection.es_connection_provider import ElasticSearchService
from .document_fetcher.provider import DocumentFetcherProvider, BulkIndexerProvider
from .elasticSearch.query_search.es_search_provider import Multi_match_search_provider
from .elasticSearch.delete_documents.delete_provider import delete_provider
__all__ = ("providers",)

providers =[ElasticSearchService,
            DocumentFetcherProvider,
            BulkIndexerProvider,
            Multi_match_search_provider,
            delete_provider]
