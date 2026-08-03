"""Multilingual Admin CMS & RAG Dashboard for Beauty Care Platform.

Serves admin.oxyjet.win interface for managing RAG knowledge base, service catalog,
RBAC user roles, audio recording toggle, and chat inspection.
"""

from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes

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


@app.get("/", response_class=HTMLResponse)
async def get_dashboard_ui() -> str:
    """Render rich, modern Glassmorphism Admin Dashboard & Landing Page."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌸 Beauty Care — Multi-Agent AI Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%);
            --card-bg: rgba(255, 255, 255, 0.05);
            --card-border: rgba(255, 255, 255, 0.1);
            --accent-pink: #ec4899;
            --accent-purple: #a855f7;
            --accent-cyan: #06b6d4;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }

        body {
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem;
            display: flex;
            justify-content: center;
        }

        .container {
            max-width: 1200px;
            width: 100%;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--card-border);
            margin-bottom: 2rem;
        }

        .logo-title {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .logo-title h1 {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(90deg, var(--accent-pink), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .badge-live {
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 0.35rem 0.8rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(12px);
            border-radius: 1rem;
            padding: 1.5rem;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .card:hover {
            transform: translateY(-4px);
            border-color: rgba(236, 72, 153, 0.4);
        }

        .card h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .subdomains-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .subdomain-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0, 0, 0, 0.2);
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.9rem;
        }

        .subdomain-item a {
            color: var(--accent-cyan);
            text-decoration: none;
            font-weight: 600;
        }

        .subdomain-item a:hover { text-decoration: underline; }

        .toggle-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--card-border);
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 26px;
        }

        .switch input { opacity: 0; width: 0; height: 0; }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: rgba(255,255,255,0.2);
            transition: .4s;
            border-radius: 34px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }

        input:checked + .slider { background-color: var(--accent-pink); }
        input:checked + .slider:before { transform: translateX(24px); }

        .agent-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }

        .pill {
            background: rgba(168, 85, 247, 0.15);
            color: var(--accent-purple);
            border: 1px solid rgba(168, 85, 247, 0.3);
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        footer {
            margin-top: 3rem;
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-muted);
            border-top: 1px solid var(--card-border);
            padding-top: 1.5rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-title">
                <h1>🌸 Beauty Care AI Platform</h1>
            </div>
            <div class="badge-live">
                <div class="pulse-dot"></div>
                LIVE on beauty.oxyjet.win
            </div>
        </header>

        <div class="grid">
            <!-- Card 1: Subdomains Architecture -->
            <div class="card">
                <h2>🌐 Production Infrastructure</h2>
                <ul class="subdomains-list">
                    <li class="subdomain-item">
                        <span>Main Salon Site</span>
                        <a href="https://beauty.oxyjet.win" target="_blank">beauty.oxyjet.win ↗</a>
                    </li>
                    <li class="subdomain-item">
                        <span>Webhooks & API</span>
                        <a href="https://beauty-api.oxyjet.win/healthz" target="_blank">beauty-api.oxyjet.win ↗</a>
                    </li>
                    <li class="subdomain-item">
                        <span>Agent Registry</span>
                        <a href="https://beauty-registry.oxyjet.win/healthz" target="_blank">beauty-registry.oxyjet.win ↗</a>
                    </li>
                    <li class="subdomain-item">
                        <span>Admin RAG CMS</span>
                        <a href="https://beauty-admin.oxyjet.win/docs" target="_blank">beauty-admin.oxyjet.win ↗</a>
                    </li>
                </ul>
            </div>

            <!-- Card 2: Micro-Agents Fleet -->
            <div class="card">
                <h2>🤖 Micro-Agents Fleet</h2>
                <p style="color: var(--text-muted); font-size: 0.9rem;">Decentralized A2A specialists with dedicated prompts and tools:</p>
                <div class="agent-pills">
                    <span class="pill">Concierge Receptionist</span>
                    <span class="pill">HairCare Specialist</span>
                    <span class="pill">Cosmetology Specialist</span>
                    <span class="pill">NailStyle Specialist</span>
                    <span class="pill">Google Maps Navigation</span>
                    <span class="pill">Marketing & LTV Retention</span>
                    <span class="pill">Reputation 5★ Booster</span>
                    <span class="pill">Google Calendar CRM</span>
                </div>
            </div>

            <!-- Card 3: Security & Audio Settings -->
            <div class="card">
                <h2>🔒 Security & Privacy (152-ФЗ)</h2>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">PII Sanitizer & De-anonymization Gateway active.</p>
                
                <div class="toggle-container">
                    <div>
                        <div style="font-weight: 600; font-size: 0.95rem;">Save Audio Recordings</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Default OFF for privacy</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="audioToggle" onchange="toggleAudio(this.checked)">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>
        </div>

        <footer>
            Beauty Care Multi-Agent Platform &copy; 2026 | GCP Project: <code>beauty-care-platform</code> | Cloudflare Universal SSL 🟧
        </footer>
    </div>

    <script>
        async function toggleAudio(enabled) {
            try {
                const res = await fetch('/api/v1/admin/settings/audio_toggle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled })
                });
                const data = await res.json();
                console.log('Audio toggle response:', data);
            } catch (err) {
                console.error('Failed to toggle audio:', err);
            }
        }
    </script>
</body>
</html>
"""


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
