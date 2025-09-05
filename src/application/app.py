from fastapi import FastAPI
from routers.root import root_routes
from services import providers
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka

def get_app():
    app=FastAPI()
    app.include_router(root_routes)

    services = [provider() for provider in providers]
    container = make_async_container(*services)
    setup_dishka(container=container, app=app)

    return app