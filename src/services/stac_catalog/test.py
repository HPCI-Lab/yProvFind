from STAC_manager import STACManager
from datetime import datetime
import asyncio
import os
import logging

logger = logging.getLogger(__name__)
async def main():
    # 1. Crea il manager


    manager = STACManager("./STAC")

    if os.path.exists("./STAC"):
        print("iizio caricamento")
        catalog= await manager.loadSTACCatalog()
        print("catalogo caricato da memeoria")
        print(catalog.to_dict())
        print("fine")
        return
    
    catalog= await manager.createSTACCataloge(        
                                        'provenance-catalog',
                                        'Catalogo di provenance e workflow'
                                        )
                                    
    # 2. Crea collection per workflow (SENZA posizione geografica)
    await manager.add_collection_to_catalog(
        collection_id='ml-training-workflows',
        description='Workflow di training ML',
        spatial_bbox=None,  # ← Nessuna posizione
        temporal_start=datetime(2024, 1, 1),
        temporal_end=None,  # Ancora in corso
        keywords=['machine-learning', 'training', 'provenance'],
        extra_fields={
            'workflow_type': 'training',
            'framework': 'pytorch'
        }
    )

    await manager.add_collection_to_catalog(
        collection_id='sentinel-2-processing',
        description='Processing Sentinel-2',
        spatial_bbox=[10.0, 45.0, 12.0, 47.0],  # ← Con posizione
        temporal_start=datetime(2023, 6, 1),
        temporal_end=datetime(2024, 1, 31),
        keywords=['sentinel-2', 'remote-sensing']
    )
    
    await manager.add_item_to_collection(
        collection_id='ml-training-workflows',
        item_id='training-run-001',
        properties={
            'model_name': 'resnet50',
            'epochs': 100,
            'accuracy': 0.94,
            'dataset': 'imagenet',
            'gpu': 'A100'
        },
        assets={
            'model': {
                'href': 's3://models/resnet50_v1.pth',
                'type': 'application/octet-stream',
                'title': 'Trained Model',
                'roles': ['model']
            },
            'logs': {
                'href': 's3://logs/training-001.log',
                'type': 'text/plain',
                'title': 'Training Logs',
                'roles': ['metadata']
            }
        },
        geometry=None,  # ← Nessuna geometria
        bbox=None,
        datetime_value=datetime(2024, 3, 15, 10, 30, 0)
    )
    
    # 5. Aggiungi altro item
    await manager.add_item_to_collection(
        collection_id='ml-training-workflows',
        item_id='training-run-002',
        properties={
            'model_name': 'efficientnet',
            'epochs': 50,
            'accuracy': 0.91,
            'dataset': 'custom',
            'gpu': 'V100'
        },
        assets={
            'model': {
                'href': 's3://models/efficientnet_v1.pth',
                'type': 'application/octet-stream',
                'roles': ['model']
            }
        },
        datetime_value=datetime(2024, 4, 20, 14, 15, 0)
    )
    
    # 6. Aggiorna extent (opzionale, ricalcola da items)
    await manager.update_collection_extent('ml-training-workflows')

    # Aggiungi item DIRETTAMENTE al catalogo (senza collection)
    item1 = await manager.add_item_to_catalog(
        item_id='workflow-run-001',
        properties={
            'workflow_name': 'data_processing',
            'status': 'success',
            'duration': 3600
        },
        assets={
            'output': {
                'href': 's3://bucket/output.csv',
                'type': 'text/csv',
                'title': 'Output Data'
            },
            'logs': {
                'href': 's3://bucket/logs.txt',
                'type': 'text/plain',
                'title': 'Logs'
            }
        },
        datetime_value=datetime(2024, 10, 20)
    )
    
    # Aggiungi altro item
    item2 = await manager.add_item_to_catalog(
        item_id='workflow-run-002',
        properties={
            'workflow_name': 'ml_training',
            'status': 'failed',
            'error': 'Out of memory'
        },
        assets={
            'logs': {
                'href': 's3://bucket/error-logs.txt',
                'type': 'text/plain'
            }
        },
        datetime_value=datetime(2024, 10, 21)
    )
    
    # Recupera tutti gli items dal catalogo
    items = await manager.get_all_items()
    print(f"\nItems nel catalogo: {len(items)}")
    for item in items:
        print(f"  - {item.id}: {item.properties}")

    collections =await manager.get_collections()
    print("collections: ")
    for coll in collections:
        print(f"{coll.title}")

    
    

    
    
    # 8. Salva
    await manager.save()
    
    print("\n✅ Tutto completato!")




if __name__=="__main__":
    asyncio.run(main())