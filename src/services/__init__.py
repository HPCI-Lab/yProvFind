from .elasticSearch.connection.es_connection_provider import ElasticSearchService
from .indexer.index_provider import  IndexerProvider
from .elasticSearch.search_documents.es_search_provider import MultiMatchSearchProvider, SemanticSearchProvider, AllDocumentsProvider
from .elasticSearch.delete_documents.delete_provider import delete_provider
from .embedding.embedding_provider import EmbeddingProvider
from .scraper.scraper_provider import ScraperProvider
from .registry.registry_provider import RegisryProvider
from .orchestration.RSEI_provider import RSEIProvider
from .orchestration.last_check_timestamp import TimestamProvider
from .elasticSearch.index_manager.index_manager_provider import IndexManagerProvider
from .elasticSearch.update_documents.update_documents_provider import UpdateDocumentsProvider
from .stac_catalog.STAC_provider import STACProvider
from .demo.demo import DemoProvider
from .orchestration.RSEI_provider import RSEIStatusProvider
__all__ = ("providers",)

providers =[ElasticSearchService,
            ScraperProvider,
            IndexerProvider,
            MultiMatchSearchProvider,
            delete_provider,
            EmbeddingProvider,
            SemanticSearchProvider,
            RegisryProvider,
            RSEIProvider,
            TimestamProvider,
            AllDocumentsProvider,
            IndexManagerProvider,
            UpdateDocumentsProvider,
            STACProvider,
            DemoProvider,
            RSEIStatusProvider
            
            ]
