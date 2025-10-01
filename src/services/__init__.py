from .elasticSearch.connection.es_connection_provider import ElasticSearchService
from .indexer.index_provider import  IndexerProvider
from .elasticSearch.search_documents.es_search_provider import MultiMatchSearchProvider, SemanticSearchProvider, AllDocumentsProvider
from .elasticSearch.delete_documents.delete_provider import delete_provider
from .embedding.embedding_provider import EmbeddingProvider
from .fetcher.fetcher_provider import DocumentFetcherProvider
from .scraper.scraper_provider import ScraperProvider
from .orchestration.SFEI_provider import SFEIProvider
from .orchestration.last_check_timestamp import TimestamProvider
from .elasticSearch.index_manager.create import IndexCreateProvider

__all__ = ("providers",)

providers =[ElasticSearchService,
            DocumentFetcherProvider,
            IndexerProvider,
            MultiMatchSearchProvider,
            delete_provider,
            EmbeddingProvider,
            SemanticSearchProvider,
            ScraperProvider,
            SFEIProvider,
            TimestamProvider,
            AllDocumentsProvider,
            IndexCreateProvider
            ]
