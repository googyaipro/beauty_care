"""Multilingual Admin CMS & RAG Dashboard for Beauty Care Platform.

Serves admin.oxyjet.win interface for managing RAG knowledge base, service catalog,
RBAC user roles, audio recording toggle, and chat inspection.
"""

from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes
from common.rbac import Role, Permission, has_permission

app = FastAPI(
    title="Beauty Care Admin CMS",
    description="Multilingual Admin Dashboard for Salon Managers & IT Super Admins",
    version="1.0.0",
)

attach_health_routes(app, service_name="beauty_care_admin_cms")

# State settings
_system_settings = {
    "save_audio_recordings": False,
    "primary_language": "en",
    "supported_languages": ["en", "ru", "ka", "de", "it", "es", "fr"],
    "payment_provider": "stripe",
}

_wiki_articles: List[Dict[str, Any]] = [
    {
        "id": "wiki_1",
        "title": "Hair Coloring Pre-Care Advice",
        "category": "hair",
        "language": "en",
        "content": "Do not wash your hair 24 hours prior to bleaching or complex coloring to protect your scalp.",
    },
    {
        "id": "wiki_2",
        "title": "Уход после чистки лица",
        "category": "cosmetology",
        "language": "ru",
        "content": "Избегайте посещения сауны, солярия и интенсивных тренировок в течение 48 часов после глубокой чистки лица.",
    },
]


class WikiArticle(BaseModel):
    title: str
    category: str
    language: str = "en"
    content: str


class AudioToggleRequest(BaseModel):
    enabled: bool


@app.get("/api/v1/admin/settings")
async def get_settings() -> Dict[str, Any]:
    """Get global platform settings."""
    return _system_settings


@app.post("/api/v1/admin/settings/audio_toggle")
async def toggle_audio_recording(req: AudioToggleRequest) -> Dict[str, Any]:
    """Toggle raw audio file retention ON/OFF."""
    _system_settings["save_audio_recordings"] = req.enabled
    return {
        "status": "updated",
        "save_audio_recordings": _system_settings["save_audio_recordings"],
        "message": f"Audio file retention is now {'ENABLED' if req.enabled else 'DISABLED'}",
    }


@app.get("/api/v1/admin/wiki")
async def list_wiki_articles() -> List[Dict[str, Any]]:
    """List all RAG Wiki articles."""
    return _wiki_articles


@app.post("/api/v1/admin/wiki", status_code=status.HTTP_201_CREATED)
async def create_wiki_article(article: WikiArticle) -> Dict[str, Any]:
    """Create a new RAG Wiki article."""
    art_id = f"wiki_{len(_wiki_articles) + 1}"
    record = {"id": art_id, **article.model_dump()}
    _wiki_articles.append(record)
    return {"status": "created", "article": record}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8019)
