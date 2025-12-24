from pystac import Catalog, Collection, Item, Asset, Extent, SpatialExtent, TemporalExtent, read_file
from pathlib import Path
import logging
from typing import Optional, List, Dict
from datetime import datetime
import os
from settings import settings

logger = logging.getLogger(__name__)



class STACManager:
    def __init__ (self):
        self.catalog= None
        self.base_path = Path(settings.STAC_BASE_PATH)
        

    def createSTACCataloge( self, 
                            id : str="catalog",
                            description: str="yProv STAC Catalog",
                            title: Optional[str] = None)-> Catalog:
        if self.catalog:
            logger.info("catalog already in memory")
            return self.catalog
        
        self.catalog= Catalog(id, description, title)
        logger.info("catalog created succesfully")
        return self.catalog
    

    def loadSTACCatalog(self)->Catalog:
        try:
            if os.path.exists(f"{self.base_path}/catalog.json"):
                self.catalog= Catalog.from_file(f"{self.base_path}/catalog.json")
                logger.info("catalog sucessfully readed")
                return self.catalog
            logger.error("catalog not present, please create one")
        except Exception as e:
            self.catalog=None
            print(f"errore {e}")
            logger.error("error durin loading of STAC cataloge ")
            return self.catalog
            

    # Ottimizza anche il metodo save per evitare operazioni ridondanti
    def save(self):
        if self.catalog is None:
            logger.warning("Catalog is None, cannot save")
            return
        
        self.catalog.normalize_hrefs(str(self.base_path))
        self.catalog.save(catalog_type='SELF_CONTAINED')
        logger.debug(f"Catalog saved in {self.base_path}")


    
    def add_collection_to_catalog(self,
                                collection_id: str,
                                description: str,
                                license: str = "proprietary",
                                spatial_bbox: Optional[List[float]] = None,
                                temporal_start: Optional[datetime] = None,
                                temporal_end: Optional[datetime] = None,
                                keywords: Optional[List[str]] = None,
                                extra_fields: Optional[Dict] = None):
        
        if spatial_bbox is None:
            spatial_extent = SpatialExtent(bboxes=[[0, 0, 0, 0]])
        else:
            spatial_extent = SpatialExtent(bboxes=[spatial_bbox])

        if temporal_start is None and temporal_end is None:
            temporal_extent = TemporalExtent(intervals=[[None, None]])
        else:
            temporal_extent = TemporalExtent(intervals=[[temporal_start, temporal_end]])


        extent=Extent(spatial=spatial_extent, temporal=temporal_extent)
        

        collection=Collection(
            id=collection_id,
            description=description,
            extent=extent,
            license=license,
            title=collection_id
        )

        if keywords:
            collection.keywords = keywords
        
        # Aggiungi campi extra se presenti
        if extra_fields:
            collection.extra_fields.update(extra_fields)
        
        # Aggiungi al catalogo
        self.catalog.add_child(collection)
        
        logger.info(f"Collection '{collection_id}' created and added to catalog")
        return collection
    

    def _find_collection(self, collection_id: str) -> Optional[Collection]:
        for child in self.catalog.get_children():
            if isinstance(child, Collection) and child.id == collection_id:
                return child
        return None
    






    def add_item_to_catalog(
            self,
            item_id: str,
            properties: Dict,
            assets: Dict[str, Dict], #l'asset anche se è uno ha la possibilta di essere piu di uno come nello standard
            geometry: Optional[Dict] = None,
            bbox: Optional[List[float]] = None,
            datetime_value: Optional[datetime] = None):
        
        if not self.catalog:
            raise ValueError("catalog not found")
        
        if geometry is None:
            geometry = {"type": "Point", "coordinates": [0, 0]}
        if bbox is None:
            bbox = [0, 0, 0, 0]

        item = Item(
            id=item_id,
            geometry=geometry,
            bbox=bbox,
            datetime=datetime_value or datetime.now(),
            properties=properties
        )

        for asset_key, asset_info in assets.items():
            item.add_asset(
                asset_key,
                Asset(
                    href=asset_info['href'],
                    media_type=asset_info.get('type'),
                    title=asset_info.get('title'),
                    roles=asset_info.get('roles')
                )
            )

        self.catalog.add_item(item)
        logger.debug(f"Item '{item_id}' aggiunto al catalogo")
        return item

    

    def add_item_to_collection(
        self,
        collection_id: str,
        item_id: str,
        properties: Dict,
        assets: Dict[str, Dict],
        geometry: Optional[Dict] = None,
        bbox: Optional[List[float]] = None,
        datetime_value: Optional[datetime] = None
    ) -> Item:
        
        collection = self._find_collection(collection_id)
        if not collection:
            raise ValueError(f"Collection '{collection_id}' not found")
        
        # Gestisci geometry e bbox per workflow (senza posizione)
        if geometry is None:
            geometry = {"type": "Point", "coordinates": [0, 0]}
        if bbox is None:
            bbox = [0, 0, 0, 0]
        
        # Crea item
        item = Item(
            id=item_id,
            geometry=geometry,
            bbox=bbox,
            datetime=datetime_value or datetime.now(),
            properties=properties
        )
        
        # Aggiungi assets
        for asset_key, asset_info in assets.items():
            item.add_asset(
                asset_key,
                Asset(
                    href=asset_info['href'],
                    media_type=asset_info.get('type'),
                    title=asset_info.get('title'),
                    roles=asset_info.get('roles')
                )
            )
        
        # Aggiungi item alla collection
        collection.add_item(item)
        
        logger.info(f"Item '{item_id}' aggiunto")
        return item
    
    def update_collection_extent(self, collection_id: str):
        logger.info(f"Aggiornamento extent per '{collection_id}'...")
        
        
        collection = self._find_collection(collection_id)
        if not collection:
            raise ValueError(f"Collection '{collection_id}' non trovata")
        
        # Aggiorna extent automaticamente dagli items
        collection.update_extent_from_items()
        
        logger.info(f"Extent aggiornato per '{collection_id}'")
        logger.debug(f"Spatial: {collection.extent.spatial.bboxes}")
        logger.debug(f"Temporal: {collection.extent.temporal.intervals}")



    def catalogListUpdate(self, batch: List[Dict]):
        errors = []

        try:
            if self.catalog is None:
                if not os.path.exists("./STAC/catalog.json"):
                    self.createSTACCataloge()
                else:
                    self.loadSTACCatalog()
        except Exception as e:
            logger.error("Is not possible to instantiate the catalog")
            raise RuntimeError("Failed to create or load STAC catalog") from e
        
        # Processa tutti gli items
        for prov in batch: 
            try:
                metadata = prov.get("_source")
                _pid = prov.get("_id")

                if _pid is None:
                    error = f"missing PID in: {prov}"
                    logger.error(error)
                    errors.append(error)
                    continue

                self.add_item_to_catalog(
                    item_id=_pid,
                    properties={
                        "provenance_version": metadata.get("version"),
                        "owner_email": metadata.get("owner"),
                        "parent_document_pid": metadata.get("parent_document_pid"),
                        "lineage_id": metadata.get("lineage", ""),
                        "title": metadata.get("title"),
                        "description": metadata.get("description"),
                        "author": metadata.get("author"),
                        "created": metadata.get("created_at")
                    },
                    assets={
                        "provenance": {
                            "href": metadata.get("storage_url"),
                            "type": "application/json",
                            "title": "Provenance file",
                            "roles": ["data"]
                        }
                    }
                )
            except Exception as e:
                error = f"Error processing item {prov.get('_id')}: {str(e)}"
                logger.error(error)
                errors.append(error)
        
        # ✅ SALVA UNA SOLA VOLTA ALLA FINE
        try:
            self.save()
        except Exception as e:
            logger.error(f"Error saving catalog: {str(e)}")
            raise

        success_count = len(batch) - len(errors)
        logger.info(f"Catalog updated with: {success_count} documents and: {len(errors)} errors")
        
        return {
            "success": success_count,
            "errors": errors
        }




            
            


    

    async def get_collections(self) -> List[Collection]:
        return list(self.catalog.get_collections())
    
    async def get_all_items(self) -> List[Item]:
        return list(self.catalog.get_all_items())
    
    async def get_catalog(self) -> Catalog:
        return self.catalog


        


