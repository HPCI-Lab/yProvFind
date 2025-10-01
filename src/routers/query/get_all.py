from typing import Annotated
from fastapi import APIRouter
from dishka.integrations.fastapi import DishkaRoute
from services.elasticSearch.search_documents.all_documents import AllDocuments
from dishka.integrations.fastapi import FromDishka



get_all_router= APIRouter(route_class=DishkaRoute,
                          prefix="",
                          tags=["search"],
                          )

@get_all_router.get("/all",
                    summary = " get all docuemnts of the index documents")
async def get_all_documents(all: Annotated[AllDocuments, FromDishka()]):
    return await all.get_all_documents()
