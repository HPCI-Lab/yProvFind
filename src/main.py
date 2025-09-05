import uvicorn
from application.app import get_app

app = get_app()


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        port=8000,
        reload=False
    )