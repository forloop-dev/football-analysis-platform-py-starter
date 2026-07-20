from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.web.pages import router as pages_router
from app.web.partials import router as partials_router


def create_app() -> FastAPI:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(pages_router)
    app.include_router(partials_router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
