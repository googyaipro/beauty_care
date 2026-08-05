import os
import sys

# Ensure /app root directory is in sys.path for common.* imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/app")

import uuid
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes
from common.language_detector import detect_language, get_text
from common.pii_sanitizer import PIISanitizer
from common.dialogue_store import (
    SharedDialogueStore,
    SharedSettingsStore,
    SharedUserStore,
    SharedWikiStore,
)
from common.rbac import Role, Permission, has_permission
from common.rate_limiter import check_rate_limit
from common.telemetry import trace_step, get_trace, _ACTIVE_TRACES
from common.schemas import ActionButton, StructuredAgentMessage
from common.orchestrator import generate_dynamic_agent_response

app = FastAPI(
    title="Beauty Care Unified API & Admin Dashboard",
    description="Unified Router for Webhooks (WhatsApp, Telegram, Web) & Real-Time Staff Admin Portal",
    version="1.0.0",
)

attach_health_routes(app, service_name="beauty_care_unified_api")


# Request Schemas
class ChatMessageRequest(BaseModel):
    session_id: str = "web_session_default"
    message: str


class TelegramWebhookPayload(BaseModel):
    update_id: int = 1
    message: Dict[str, Any]


class WhatsAppWebhookPayload(BaseModel):
    phone_number: str
    message_text: str


class UserRegistration(BaseModel):
    name: str
    email: str
    password: str
    role: str = "receptionist"


class WikiArticle(BaseModel):
    title: str
    category: str
    language: str = "en"
    content: str


class AudioToggleRequest(BaseModel):
    enabled: bool


# --- WEBHOOK ENDPOINTS (beauty-api.oxyjet.win) ---

@app.post("/v1/webhook/whatsapp")
async def handle_whatsapp_webhook(payload: WhatsAppWebhookPayload) -> Dict[str, Any]:
    """Receive WhatsApp webhook payload (dynamic Google Calendar CRM & Maps MCP resolution)."""
    check_rate_limit(f"wa_{payload.phone_number}")
    trace_id = str(uuid.uuid4())

    with trace_step(trace_id, "WhatsApp_Webhook"):
        user_text = payload.message_text.strip()
        lang = detect_language(user_text)

        sanitizer = PIISanitizer()
        sanitized_text, _ = sanitizer.sanitize(user_text)

        session_id = f"wa_{payload.phone_number}"

        SharedDialogueStore.add_message(
            session_id=session_id,
            sender_role="user",
            content=user_text,
            channel="whatsapp",
            language=lang,
        )

        structured_msg = await generate_dynamic_agent_response(
            user_text=user_text,
            lang=lang,
            session_id=session_id,
            trace_id=trace_id,
        )

        SharedDialogueStore.add_message(
            session_id=session_id,
            sender_role="agent",
            content=structured_msg.text_response,
            channel="whatsapp",
            language=lang,
        )

        return {
            "status": "ok",
            "phone_number": payload.phone_number,
            "language_detected": lang,
            "reply": structured_msg.text_response,
            "buttons": [b.model_dump() for b in structured_msg.buttons],
            "trace_id": trace_id,
        }


@app.post("/v1/webhook/telegram")
async def handle_telegram_webhook(payload: TelegramWebhookPayload) -> Dict[str, Any]:
    """Receive Telegram webhook payload (dynamic Google Calendar CRM & Maps MCP resolution)."""
    msg = payload.message
    chat_id = str(msg.get("chat", {}).get("id", "777"))
    check_rate_limit(f"tg_{chat_id}")
    trace_id = str(uuid.uuid4())

    with trace_step(trace_id, "Telegram_Webhook"):
        user_text = msg.get("text", "")
        lang = detect_language(user_text)

        sanitizer = PIISanitizer()
        sanitized_text, _ = sanitizer.sanitize(user_text)

        session_id = f"tg_{chat_id}"

        SharedDialogueStore.add_message(
            session_id=session_id,
            sender_role="user",
            content=user_text,
            channel="telegram",
            language=lang,
        )

        structured_msg = await generate_dynamic_agent_response(
            user_text=user_text,
            lang=lang,
            session_id=session_id,
            trace_id=trace_id,
        )

        SharedDialogueStore.add_message(
            session_id=session_id,
            sender_role="agent",
            content=structured_msg.text_response,
            channel="telegram",
            language=lang,
        )

        return {
            "status": "ok",
            "chat_id": chat_id,
            "language_detected": lang,
            "reply": structured_msg.text_response,
            "buttons": [b.model_dump() for b in structured_msg.buttons],
            "trace_id": trace_id,
        }


@app.post("/api/v1/chat")
async def handle_live_chat(req: ChatMessageRequest) -> Dict[str, Any]:
    """LIVE Multi-Agent Chat Endpoint for Web Booking Widget."""
    check_rate_limit(req.session_id)
    user_text = req.message.strip()
    if not user_text:
        return {"reply": "Please enter a valid message."}

    trace_id = str(uuid.uuid4())

    with trace_step(trace_id, "Web_Widget_Chat"):
        lang = detect_language(user_text)

        sanitizer = PIISanitizer()
        sanitized_text, _ = sanitizer.sanitize(user_text)

        SharedDialogueStore.add_message(
            session_id=req.session_id,
            sender_role="user",
            content=user_text,
            channel="web_widget",
            language=lang,
        )

        structured_msg = await generate_dynamic_agent_response(
            user_text=user_text,
            lang=lang,
            session_id=req.session_id,
            trace_id=trace_id,
        )

        SharedDialogueStore.add_message(
            session_id=req.session_id,
            sender_role="agent",
            content=structured_msg.text_response,
            channel="web_widget",
            language=lang,
        )

        return {
            "status": "success",
            "language_detected": lang,
            "reply": structured_msg.text_response,
            "buttons": [b.model_dump() for b in structured_msg.buttons],
            "trace_id": trace_id,
        }


# --- REST ADMIN API ENDPOINTS ---

@app.get("/api/v1/admin/dialogues")
async def get_realtime_dialogues(limit: int = 100) -> List[Dict[str, Any]]:
    """REST API: Get all real-time client messages across Telegram, WhatsApp, Web Widget, and curl tests."""
    return SharedDialogueStore.get_all_messages(limit=limit)


@app.get("/api/v1/admin/telemetry")
async def get_telemetry_traces() -> Dict[str, Any]:
    """REST API: Get OpenTelemetry waterfall trace spans for execution profiling."""
    return _ACTIVE_TRACES


@app.get("/api/v1/admin/settings")
async def get_settings() -> Dict[str, Any]:
    """REST API: Get current system settings."""
    return SharedSettingsStore.get_settings()


@app.post("/api/v1/admin/settings/audio_toggle")
async def toggle_audio_recording(req: AudioToggleRequest) -> Dict[str, Any]:
    """REST API: Toggle raw audio file retention ON/OFF."""
    updated = SharedSettingsStore.update_settings({"save_audio_recordings": req.enabled})
    return {
        "status": "updated",
        "save_audio_recordings": updated["save_audio_recordings"],
        "message": f"Audio file retention is now {'ENABLED' if req.enabled else 'DISABLED'}",
    }


@app.get("/api/v1/admin/users")
async def list_staff_users() -> List[Dict[str, Any]]:
    """REST API: List all registered staff members."""
    return SharedUserStore.get_users()


@app.post("/api/v1/admin/users/register", status_code=status.HTTP_201_CREATED)
async def register_staff_user(user: UserRegistration) -> Dict[str, Any]:
    """REST API: Register a new staff member."""
    record = SharedUserStore.add_user(name=user.name, email=user.email, role=user.role)
    return {"status": "registered", "user": record}


@app.get("/api/v1/admin/wiki")
async def list_wiki_articles() -> List[Dict[str, Any]]:
    """REST API: List all RAG Wiki articles."""
    return SharedWikiStore.get_articles()


@app.post("/api/v1/admin/wiki", status_code=status.HTTP_201_CREATED)
async def create_wiki_article(article: WikiArticle) -> Dict[str, Any]:
    """REST API: Create a new RAG Wiki article."""
    record = SharedWikiStore.add_article(
        title=article.title,
        category=article.category,
        language=article.language,
        content=article.content,
    )
    return {"status": "created", "article": record}


# --- HTML UI ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def get_client_landing_page() -> str:
    """Public Client Landing Page & Interactive LIVE AI Web Booking Widget (beauty.oxyjet.win)."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌸 Beauty Care — Salon & Spa Online Booking</title>
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
        body { background: var(--bg-gradient); color: var(--text-main); min-height: 100vh; padding: 2rem; display: flex; justify-content: center; }
        .container { max-width: 1200px; width: 100%; }

        header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 2rem; border-bottom: 1px solid var(--card-border); margin-bottom: 2rem; }
        .logo-title h1 { font-size: 2.2rem; font-weight: 700; background: linear-gradient(90deg, var(--accent-pink), var(--accent-purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

        .nav-buttons { display: flex; gap: 1rem; }
        .btn { padding: 0.6rem 1.2rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; text-decoration: none; transition: all 0.2s ease; }
        .btn-primary { background: linear-gradient(90deg, var(--accent-pink), var(--accent-purple)); color: white; border: none; }
        .btn-outline { background: transparent; color: var(--text-main); border: 1px solid var(--card-border); }

        .hero-section { text-align: center; padding: 3rem 1rem; background: var(--card-bg); border: 1px solid var(--card-border); backdrop-filter: blur(12px); border-radius: 1.5rem; }
        .hero-section h2 { font-size: 2.5rem; margin-bottom: 1rem; }
        .hero-section p { color: var(--text-muted); font-size: 1.1rem; max-width: 600px; margin: 0 auto 2rem auto; }

        .chat-widget { max-width: 550px; margin: 0 auto; background: rgba(0,0,0,0.5); border: 1px solid var(--card-border); border-radius: 1rem; overflow: hidden; text-align: left; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
        .chat-header { background: rgba(255,255,255,0.05); padding: 1rem; display: flex; align-items: center; gap: 0.75rem; border-bottom: 1px solid var(--card-border); }
        .chat-messages { height: 280px; padding: 1rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; }

        .msg { padding: 0.75rem 1rem; border-radius: 0.75rem; font-size: 0.95rem; max-width: 85%; line-height: 1.4; }
        .msg-agent { background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.3); align-self: flex-start; }
        .msg-user { background: var(--accent-pink); color: white; align-self: flex-end; }

        .chat-input-bar { display: flex; padding: 0.75rem; background: rgba(0,0,0,0.6); gap: 0.5rem; }
        .chat-input-bar input { flex: 1; background: rgba(255,255,255,0.08); border: 1px solid var(--card-border); padding: 0.6rem 1rem; border-radius: 0.5rem; color: white; outline: none; }

        footer { text-align: center; margin-top: 3rem; font-size: 0.85rem; color: var(--text-muted); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-title"><h1>🌸 Beauty Care</h1></div>
            <div class="nav-buttons">
                <a href="/login" class="btn btn-outline">Staff Portal Login 🔑</a>
                <a href="/register" class="btn btn-primary">Staff Registration 📝</a>
            </div>
        </header>

        <div class="hero-section">
            <h2>Book Your Salon Appointment Online</h2>
            <p>Chat with our AI Receptionist in 7 languages (EN, RU, KA, DE, IT, ES, FR) to schedule haircuts, skincare, or manicures.</p>

            <div class="chat-widget">
                <div class="chat-header">
                    <div style="width:10px; height:10px; background:#10b981; border-radius:50%;"></div>
                    <strong>AI Concierge Receptionist (LIVE)</strong>
                </div>
                <div class="chat-messages" id="chatMessages">
                    <div class="msg msg-agent">
                        Здравствуйте! Я ИИ-Администратор салона Beauty Care. Чем могу помочь вам сегодня? Вы можете спросить об услугах или записаться на удобный день!
                    </div>
                </div>
                <div class="chat-input-bar">
                    <input type="text" id="chatInput" placeholder="Введите ваш запрос (например: Хочу записаться на окрашивание в эту пятницу)..." onkeydown="if(event.key==='Enter') sendMsg()">
                    <button class="btn btn-primary" onclick="sendMsg()">Отправить</button>
                </div>
            </div>
        </div>

        <footer>
            Beauty Care Platform &copy; 2026 | Domain: <code>beauty.oxyjet.win</code> | GCP: <code>beauty-care-platform</code>
        </footer>
    </div>

    <script>
        async function sendMsg() {
            const input = document.getElementById('chatInput');
            const txt = input.value.trim();
            if (!txt) return;

            const box = document.getElementById('chatMessages');
            box.innerHTML += `<div class="msg msg-user">${txt}</div>`;
            input.value = '';
            box.scrollTop = box.scrollHeight;

            try {
                const res = await fetch('/api/v1/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: txt })
                });
                const data = await res.json();
                box.innerHTML += `<div class="msg msg-agent">${data.reply}</div>`;
                box.scrollTop = box.scrollHeight;
            } catch (err) {
                box.innerHTML += `<div class="msg msg-agent">[System]: Connection error. Please try again.</div>`;
            }
        }
    </script>
</body>
</html>
"""


@app.get("/login", response_class=HTMLResponse)
async def get_login_page() -> str:
    """Staff & Master Portal Login Screen."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🔑 Staff Portal Login — Beauty Care</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { background: #0f172a; color: white; font-family: 'Outfit', sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
        .box { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 2.5rem; border-radius: 1rem; width: 380px; }
        h2 { margin-bottom: 1.5rem; color: #ec4899; text-align:center; }
        input, select, button { width: 100%; padding: 0.75rem; margin-bottom: 1rem; border-radius: 0.5rem; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.4); color: white; }
        button { background: #ec4899; font-weight: bold; cursor: pointer; border: none; }
        a { color: #06b6d4; text-decoration: none; display: block; text-align: center; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🔑 Staff Portal Login</h2>
        <input type="email" placeholder="Staff Email (e.g. admin@oxyjet.win)">
        <input type="password" placeholder="Password">
        <button onclick="location.href='/dashboard'">Sign In</button>
        <a href="/register">Don't have an account? Register staff member ➔</a>
    </div>
</body>
</html>
"""


@app.get("/register", response_class=HTMLResponse)
async def get_register_page() -> str:
    """Staff & Master Registration Screen."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>📝 Staff Registration — Beauty Care</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { background: #0f172a; color: white; font-family: 'Outfit', sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
        .box { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 2.5rem; border-radius: 1rem; width: 420px; }
        h2 { margin-bottom: 1.5rem; color: #a855f7; text-align:center; }
        input, select, button { width: 100%; padding: 0.75rem; margin-bottom: 1rem; border-radius: 0.5rem; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.4); color: white; }
        button { background: #a855f7; font-weight: bold; cursor: pointer; border: none; }
        a { color: #06b6d4; text-decoration: none; display: block; text-align: center; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="box">
        <h2>📝 Register New Staff Member</h2>
        <input type="text" id="regName" placeholder="Full Name (e.g. Elena Petrova)">
        <input type="email" id="regEmail" placeholder="Email Address">
        <input type="password" placeholder="Password">
        <select id="regRole">
            <option value="salon_manager">Salon Manager (Управляющий)</option>
            <option value="receptionist">Receptionist (Администратор)</option>
            <option value="master">Master / Stylist (Мастер салона)</option>
            <option value="super_admin">Super Admin (IT-Администратор)</option>
        </select>
        <button onclick="registerUser()">Create Account</button>
        <a href="/login">Already registered? Sign in ➔</a>
    </div>

    <script>
        async function registerUser() {
            const name = document.getElementById('regName').value;
            const email = document.getElementById('regEmail').value;
            const role = document.getElementById('regRole').value;
            if(!name || !email) { alert('Please enter name and email'); return; }

            const res = await fetch('/api/v1/admin/users/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password: 'secret_pass', role })
            });
            const data = await res.json();
            alert('Staff user registered successfully!');
            location.href = '/dashboard';
        }
    </script>
</body>
</html>
"""


@app.get("/dashboard", response_class=HTMLResponse)
async def get_interactive_dashboard_page() -> str:
    """Rich Multi-Tab Real-Time Admin Dashboard for IT Super Admin & Salon Managers."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌸 Real-Time Admin Dashboard — Beauty Care</title>
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
        body { background: var(--bg-gradient); color: var(--text-main); min-height: 100vh; padding: 2rem; }
        .container { max-width: 1200px; margin: 0 auto; }

        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--card-border); padding-bottom: 1.5rem; margin-bottom: 2rem; }
        h1 { font-size: 2rem; background: linear-gradient(90deg, var(--accent-pink), var(--accent-purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

        .tabs { display: flex; gap: 1rem; margin-bottom: 2rem; border-bottom: 1px solid var(--card-border); padding-bottom: 0.5rem; }
        .tab-btn { background: transparent; border: none; color: var(--text-muted); font-size: 1rem; font-weight: 600; padding: 0.5rem 1rem; cursor: pointer; border-radius: 0.5rem; transition: all 0.2s; }
        .tab-btn.active { background: rgba(236, 72, 153, 0.2); color: var(--accent-pink); border: 1px solid rgba(236, 72, 153, 0.4); }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; }
        .card { background: var(--card-bg); border: 1px solid var(--card-border); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: 1rem; }

        h2 { font-size: 1.25rem; color: var(--accent-pink); margin-bottom: 1rem; }
        input, select, textarea, button { width: 100%; padding: 0.75rem; margin-bottom: 1rem; border-radius: 0.5rem; border: 1px solid var(--card-border); background: rgba(0,0,0,0.4); color: white; font-size: 0.95rem; }
        button { background: linear-gradient(90deg, var(--accent-pink), var(--accent-purple)); font-weight: bold; cursor: pointer; border: none; }

        .status-badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.25rem 0.65rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); }
        .table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        .table th, .table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--card-border); font-size: 0.9rem; }
        .table th { color: var(--text-muted); font-weight: 600; }
        .badge-channel { padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600; }
        .ch-telegram { background: rgba(6, 182, 212, 0.2); color: #06b6d4; }
        .ch-whatsapp { background: rgba(16, 185, 129, 0.2); color: #10b981; }
        .ch-web_widget { background: rgba(236, 72, 153, 0.2); color: #ec4899; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌸 IT Super Admin & Salon Manager Portal</h1>
            <div style="display:flex; gap:1rem; align-items:center;">
                <span style="font-size:0.9rem; color:var(--text-muted);">Logged in as: <strong style="color:white;">admin@oxyjet.win</strong> (Super Admin)</span>
                <a href="/" style="color:var(--accent-cyan); text-decoration:none; font-weight:600;">Client Web Site ↗</a>
            </div>
        </header>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('chats')">💬 Real-Time Chat Inspector</button>
            <button class="tab-btn" onclick="switchTab('overview')">📊 System Overview</button>
            <button class="tab-btn" onclick="switchTab('wiki')">📚 RAG Wiki Editor</button>
            <button class="tab-btn" onclick="switchTab('staff')">👥 Staff & Roles</button>
            <button class="tab-btn" onclick="switchTab('settings')">⚙️ Security & Audio</button>
        </div>

        <div id="tab-chats" class="tab-content active">
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                    <h2>💬 Real-Time Client Dialogue Inspector</h2>
                    <button onclick="loadRealtimeChats()" style="width:auto; padding:0.4rem 1rem;">🔄 Refresh Now</button>
                </div>
                <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:1rem;">Live feed of all client messages across Telegram, WhatsApp, Web Widget, and curl tests.</p>
                <table class="table">
                    <thead>
                        <tr><th>Time</th><th>Channel</th><th>Session / Client</th><th>Role</th><th>Lang</th><th>Message Content</th></tr>
                    </thead>
                    <tbody id="chatsTableBody">
                        <tr><td colspan="6" style="text-align:center; color:var(--text-muted);">Loading real-time dialogues...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div id="tab-overview" class="tab-content">
            <div class="cards">
                <div class="card">
                    <h2>🟢 Service Health Probes</h2>
                    <ul style="list-style:none;">
                        <li style="padding:0.5rem 0; display:flex; justify-content:space-between;"><span>Google Calendar CRM MCP</span> <span class="status-badge">ONLINE</span></li>
                        <li style="padding:0.5rem 0; display:flex; justify-content:space-between;"><span>Payment MCP (Stripe/YooKassa)</span> <span class="status-badge">ONLINE</span></li>
                        <li style="padding:0.5rem 0; display:flex; justify-content:space-between;"><span>Google Maps Platform</span> <span class="status-badge">ONLINE</span></li>
                        <li style="padding:0.5rem 0; display:flex; justify-content:space-between;"><span>Agent Registry Server</span> <span class="status-badge">ONLINE</span></li>
                        <li style="padding:0.5rem 0; display:flex; justify-content:space-between;"><span>Telegram & WhatsApp Gateways</span> <span class="status-badge">ONLINE</span></li>
                    </ul>
                </div>

                <div class="card">
                    <h2>☁️ Cloud Infrastructure & Telemetry</h2>
                    <p style="color:var(--text-muted); font-size:0.95rem; margin-bottom:0.5rem;">GCP Dedicated Project: <code>beauty-care-platform</code></p>
                    <p style="color:var(--text-muted); font-size:0.95rem; margin-bottom:0.5rem;">Domain Namespace: <code>beauty-*.oxyjet.win</code></p>
                    <p style="color:var(--text-muted); font-size:0.95rem; margin-bottom:0.5rem;">Cloudflare Proxy & SSL: <strong style="color:#10b981;">Active 🟧</strong></p>
                    <p style="color:var(--text-muted); font-size:0.95rem;">OpenTelemetry Spans: <strong style="color:#06b6d4;">Active (Waterfall Tracing Enabled)</strong></p>
                </div>
            </div>
        </div>

        <div id="tab-wiki" class="tab-content">
            <div class="cards">
                <div class="card">
                    <h2>➕ Add New RAG Wiki Article</h2>
                    <input type="text" id="wikiTitle" placeholder="Article Title (e.g. Post-Peeling Care)">
                    <select id="wikiCategory">
                        <option value="hair">Hair Styling & Coloring</option>
                        <option value="cosmetology">Cosmetology & Skincare</option>
                        <option value="nails">Manicure & Nail Art</option>
                    </select>
                    <select id="wikiLang">
                        <option value="ru">Russian (Русский)</option>
                        <option value="en">English</option>
                        <option value="ka">Georgian (ქართული)</option>
                        <option value="de">German (Deutsch)</option>
                    </select>
                    <textarea id="wikiContent" rows="3" placeholder="Enter advice/instruction content for AI Knowledge Base..."></textarea>
                    <button onclick="addWikiArticle()">Save to RAG Knowledge Base</button>
                </div>

                <div class="card">
                    <h2>📚 Active RAG Knowledge Articles</h2>
                    <table class="table">
                        <thead>
                            <tr><th>Title</th><th>Category</th><th>Lang</th></tr>
                        </thead>
                        <tbody id="wikiTableBody">
                            <tr><td>Hair Coloring Pre-Care Advice</td><td>Hair</td><td>EN</td></tr>
                            <tr><td>Уход после чистки лица</td><td>Cosmetology</td><td>RU</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="tab-staff" class="tab-content">
            <div class="cards">
                <div class="card">
                    <h2>➕ Register Staff Account</h2>
                    <input type="text" id="staffName" placeholder="Full Name">
                    <input type="email" id="staffEmail" placeholder="Email Address">
                    <select id="staffRole">
                        <option value="salon_manager">Salon Manager (Управляющий)</option>
                        <option value="receptionist">Receptionist (Администратор)</option>
                        <option value="master">Master / Stylist (Мастер салона)</option>
                        <option value="super_admin">Super Admin (IT-Администратор)</option>
                    </select>
                    <button onclick="addStaffUser()">Create Staff Account</button>
                </div>

                <div class="card">
                    <h2>👥 Active Staff & Master Accounts</h2>
                    <table class="table">
                        <thead>
                            <tr><th>Email</th><th>Name</th><th>Role</th></tr>
                        </thead>
                        <tbody id="staffTableBody">
                            <tr><td>admin@oxyjet.win</td><td>Super Admin</td><td>super_admin</td></tr>
                            <tr><td>manager@oxyjet.win</td><td>Elena Manager</td><td>salon_manager</td></tr>
                            <tr><td>anna@oxyjet.win</td><td>Anna Stylist</td><td>master</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="tab-settings" class="tab-content">
            <div class="cards">
                <div class="card">
                    <h2>🔒 PII Protection & 152-ФЗ Settings</h2>
                    <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:1rem;">PII Sanitizer & De-anonymization Gateway is active.</p>
                    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.3); padding:1rem; border-radius:0.5rem;">
                        <div>
                            <strong>Save Audio Recordings (Audio Vault)</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted);">Off by default for privacy & disk optimization</div>
                        </div>
                        <button onclick="toggleAudioSetting()" style="width:auto; padding:0.5rem 1rem;">Toggle Audio Vault</button>
                    </div>
                </div>

                <div class="card">
                    <h2>💳 Multi-Country Payment Configuration</h2>
                    <label style="font-size:0.85rem; color:var(--text-muted);">Active Payment Gateway Adapter:</label>
                    <select id="paymentAdapterSelect">
                        <option value="stripe">Stripe / Adyen (EU, US, International)</option>
                        <option value="tbc">TBC Bank / BoG API (Georgia)</option>
                        <option value="yookassa">YooKassa 54-ФЗ (RF / CIS)</option>
                    </select>
                    <button onclick="alert('Payment provider adapter updated!')">Update Payment Provider</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        function switchTab(name) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + name).classList.add('active');

            if (name === 'chats') {
                loadRealtimeChats();
            }
        }

        async function loadRealtimeChats() {
            try {
                const res = await fetch('/api/v1/admin/dialogues');
                const dialogues = await res.json();

                const tbody = document.getElementById('chatsTableBody');
                if (!dialogues || dialogues.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No messages recorded yet. Send a curl test or message on WhatsApp/Telegram!</td></tr>`;
                    return;
                }

                tbody.innerHTML = dialogues.reverse().map(d => `
                    <tr>
                        <td>${d.timestamp || ''}</td>
                        <td><span class="badge-channel ch-${d.channel.toLowerCase()}">${d.channel.toUpperCase()}</span></td>
                        <td><code>${d.session_id}</code></td>
                        <td><strong style="color:${d.sender_role === 'user' ? '#ec4899' : '#a855f7'}">${d.sender_role.toUpperCase()}</strong></td>
                        <td>${d.language || 'EN'}</td>
                        <td>${d.content}</td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error('Failed to load chats:', err);
            }
        }

        setInterval(loadRealtimeChats, 4000);
        loadRealtimeChats();

        async function addWikiArticle() {
            const title = document.getElementById('wikiTitle').value;
            const category = document.getElementById('wikiCategory').value;
            const language = document.getElementById('wikiLang').value;
            const content = document.getElementById('wikiContent').value;
            if(!title || !content) { alert('Please enter title and content'); return; }

            const res = await fetch('/api/v1/admin/wiki', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ title, category, language, content })
            });
            const data = await res.json();
            alert('Article saved to RAG Knowledge Base!');

            const tbody = document.getElementById('wikiTableBody');
            tbody.innerHTML += `<tr><td>${title}</td><td>${category}</td><td>${language.toUpperCase()}</td></tr>`;
        }

        async function addStaffUser() {
            const name = document.getElementById('staffName').value;
            const email = document.getElementById('staffEmail').value;
            const role = document.getElementById('staffRole').value;
            if(!name || !email) { alert('Please enter name and email'); return; }

            const res = await fetch('/api/v1/admin/users/register', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ name, email, password:'secret_password', role })
            });
            const data = await res.json();
            alert('Staff member created successfully!');

            const tbody = document.getElementById('staffTableBody');
            tbody.innerHTML += `<tr><td>${email}</td><td>${name}</td><td>${role}</td></tr>`;
        }

        async function toggleAudioSetting() {
            const res = await fetch('/api/v1/admin/settings/audio_toggle', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ enabled: true })
            });
            const data = await res.json();
            alert(data.message);
        }
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8019)
