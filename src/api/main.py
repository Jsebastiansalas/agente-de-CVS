"""Aplicación FastAPI principal sirviendo la API REST y el Dashboard MVP (HU-4.1, HU-4.2)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from src.api.routes import router

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    """Construye la instancia de la aplicación FastAPI."""
    application = FastAPI(
        title="Agente Evaluador de CVs vs. Vacantes",
        description=(
            "API REST y Dashboard para evaluar Hojas de Vida contra Vacantes "
            "usando LangGraph, Gemini y scoring determinista."
        ),
        version="0.1.0",
    )
    application.include_router(router)

    @application.get("/", include_in_schema=False)
    def serve_dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return application


app = create_app()
