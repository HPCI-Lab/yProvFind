from services.registry.registry import RegistryService
from typing import Annotated
from fastapi import APIRouter
from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka
from pydantic import BaseModel, HttpUrl, field_validator
from urllib.parse import urlparse


registry_router=APIRouter(route_class= DishkaRoute,
                          prefix="/registry",
                          tags=["Registry"])



class AddressInput(BaseModel):
    address: HttpUrl  # Validazione automatica URL da Pydantic
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        url_str = str(v)
        parsed = urlparse(url_str)
        
        # Controlla che abbia schema http/https
        if parsed.scheme not in ['http', 'https']:
            raise ValueError('Lo schema deve essere http o https')
        
        # Controlla che abbia un hostname valido
        if not parsed.netloc:
            raise ValueError('URL deve avere un hostname valido')
        

        """"
        #bloccare l'host locale
        blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
        if parsed.netloc.split(':')[0] in blocked_hosts:
            raise ValueError('Non è possibile usare localhost')
        """


        return url_str

class RegistryUpdateResponse(BaseModel):
    status: str
    address: str
    total_addresses: int


@registry_router.post("/update-list", response_model=RegistryUpdateResponse)
async def add_address_endpoint(address_input: AddressInput, registry: Annotated[RegistryService, FromDishka()]):
    result = registry.update_address_list(str(address_input.address))
    return result



@registry_router.get("/get-address-list", description="returns the list of all addresses saved in memory, both active and inactive")
def get_all_addresses_list(registry: Annotated[RegistryService, FromDishka()]):
    return registry.get_all_list()


@registry_router.get("/get-active-addresses", description="returns the list of active addresses")
def get_active_addresses_list(registry: Annotated[RegistryService, FromDishka()]):
    return registry.get_active_list()


@registry_router.get("/update-active-addresses", description="update and returns the list of active addresses")
def update_addresses_list(registry: Annotated[RegistryService, FromDishka()]):
    registry.update_active_list()
    return registry.get_active_list()


@registry_router.delete("/delete-address")
def delete_address(address: str, registry: Annotated[RegistryService, FromDishka()]):
    return registry.delete_address(address)