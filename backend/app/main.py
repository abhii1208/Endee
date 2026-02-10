from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from backend.app.api import routes_health, routes_ingest, routes_search
from backend.app.config import get_settings
from backend.app.services.endee_client import get_endee_client


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    app.include_router(routes_health.router)
    app.include_router(routes_ingest.router)
    app.include_router(routes_search.router)

    base_dir = Path(__file__).resolve().parent
    templates = Jinja2Templates(directory=str(base_dir / "templates"))

    static_dir = base_dir / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "environment": settings.environment,
            },
        )

    @app.on_event("startup")
    async def on_startup():
        logger.info("Initialising Endee client on startup.")
        get_endee_client()

    return app


app = create_app()

