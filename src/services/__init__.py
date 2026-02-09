from .elasticSearch.connection.es_connection_provider import ElasticSearchService
from .indexer.index_provider import  IndexerProvider
from .elasticSearch.search_service.es_search_provider import MultiMatchSearchProvider, SemanticSearchProvider, AllDocumentsProvider
from .elasticSearch.delete_documents.delete_provider import delete_provider
from .embedding.embedding_provider import EmbeddingProvider
from .scraper.scraper_provider import ScraperProvider
from .registry.registry_provider import RegisryProvider
from .orchestration.RSEI_provider import RSEIProvider
from .orchestration.last_check_timestamp import TimestamProvider
from .elasticSearch.index_manager.index_manager_provider import IndexManagerProvider
from .stac_catalog.STAC_provider import STACProvider
from .demo.demo import DemoProvider
from .orchestration.RSEI_provider import RSEIStatusProvider
from .elasticSearch.file_counter.file_counter import FileCounterProvider
from .LLM.llm_provider import LLMProvider
from .metadata_enricher.prov_analyzer import AnalyzerProvider
from .metadata_enricher.meta_enricher_provider import MetaEnricherProvider
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
            STACProvider,
            DemoProvider,
            RSEIStatusProvider,
            FileCounterProvider,
            LLMProvider,
            AnalyzerProvider,
            MetaEnricherProvider
            ]
