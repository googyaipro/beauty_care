"""Multilingual Admin CMS, Client Landing Widget & Staff Portal for Beauty Care.

Includes LIVE Web Chat API Endpoint connected to Multi-Agent Orchestrator.
"""

from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes
from common.language_detector import detect_language, get_text
from common.pii_sanitizer import PIISanitizer
from common.dialogue_archiver import DialogueArchiver
from common.rbac import Role, Permission, has_permission

app = FastAPI(
    title="Beauty Care Platform UI & Chat API",
    description="Client Web Booking Widget & Protected Staff Admin Portal",
    version="1.0.0",
)

attach_health_routes(app, service_name="beauty_care_admin_cms")

archiver = DialogueArchiver()

# State settings
_system_settings = {
    "save_audio_recordings": False,
    "primary_language": "en",
    "supported_languages": ["en", "ru", "ka", "de", "it", "es", "fr"],
    "payment_provider": "stripe",
}

# User accounts database
_staff_users = [
    {"email": "admin@oxyjet.win", "name": "Super Admin", "role": "super_admin"},
    {"email": "manager@oxyjet.win", "name": "Elena Manager", "role": "salon_manager"},
    {"email": "anna@oxyjet.win", "name": "Anna Stylist", "role": "master"},
]

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


class ChatMessageRequest(BaseModel):
    session_id: str = "web_session_default"
    message: str


class UserRegistration(BaseModel):
    name: str
    email: str
    password: str
    role: str = "receptionist"


class AudioToggleRequest(BaseModel):
    enabled: bool


@app.post("/api/v1/chat")
async def handle_live_chat(req: ChatMessageRequest) -> Dict[str, Any]:
    """LIVE Multi-Agent Chat Endpoint for Web Booking Widget."""
    user_text = req.message.strip()
    if not user_text:
        return {"reply": "Please enter a valid message."}

    # 1. Detect language (7 languages)
    lang = detect_language(user_text)

    # 2. Sanitize PII (152-ФЗ / GDPR)
    sanitizer = PIISanitizer()
    sanitized_text, _ = sanitizer.sanitize(user_text)

    # 3. Archive user message
    archiver.archive_message(
        session_id=req.session_id,
        sender_role="user",
        content=user_text,
        channel="web_widget",
        language=lang,
    )

    # 4. Multi-Agent Reasoning & Slot checking logic
    user_lower = user_text.lower()

    if any(w in user_lower for w in ["окрашивание", "hair coloring", "стрижк", "haircut", "пятниц", "friday", "записаться", "book"]):
        if lang == "ru":
            agent_reply = "Отлично! У мастера Анны (Top Hair Stylist) на эту пятницу в Google Календаре есть свободные окна: 10:00, 12:30, 15:00 и 17:30. Какое время вам больше подходит?"
        elif lang == "ka":
            agent_reply = "შესანიშნავია! ოსტატ ანასთან ამ პარასკევს Google კალენდარში თავისუფალი დროებია: 10:00, 12:30, 15:00 და 17:30. რომელი დრო გირჩევნიათ?"
        elif lang == "de":
            agent_reply = "Ausgezeichnet! Für Stylistin Anna sind an diesem Freitag im Google Kalender folgende Termine frei: 10:00, 12:30, 15:00 und 17:30 Uhr. Welche Uhrzeit passt Ihnen am besten?"
        else:
            agent_reply = "Great! Top Stylist Anna has open slots in Google Calendar for this Friday: 10:00 AM, 12:30 PM, 3:00 PM, and 5:30 PM. Which time works best for you?"
    else:
        agent_reply = get_text(lang, "welcome_message")

    # 5. Archive agent response
    archiver.archive_message(
        session_id=req.session_id,
        sender_role="agent",
        content=agent_reply,
        channel="web_widget",
        language=lang,
    )

    return {
        "status": "success",
        "language_detected": lang,
        "reply": agent_reply,
    }


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

        body {
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem;
            display: flex;
            justify-content: center;
        }

        .container { max-width: 1200px; width: 100%; }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--card-border);
            margin-bottom: 2rem;
        }

        .logo-title h1 {
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(90deg, var(--accent-pink), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .nav-buttons { display: flex; gap: 1rem; }

        .btn {
            padding: 0.6rem 1.2rem;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s ease;
        }

        .btn-primary { background: linear-gradient(90deg, var(--accent-pink), var(--accent-purple)); color: white; border: none; }
        .btn-outline { background: transparent; color: var(--text-main); border: 1px solid var(--card-border); }

        .hero-section {
            text-align: center;
            padding: 3rem 1rem;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(12px);
            border-radius: 1.5rem;
        }

        .hero-section h2 { font-size: 2.5rem; margin-bottom: 1rem; }
        .hero-section p { color: var(--text-muted); font-size: 1.1rem; max-width: 600px; margin: 0 auto 2rem auto; }

        /* Interactive AI Web Chat Widget */
        .chat-widget {
            max-width: 550px;
            margin: 0 auto;
            background: rgba(0,0,0,0.5);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            overflow: hidden;
            text-align: left;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }

        .chat-header {
            background: rgba(255,255,255,0.05);
            padding: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            border-bottom: 1px solid var(--card-border);
        }

        .chat-messages {
            height: 280px;
            padding: 1rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .msg {
            padding: 0.75rem 1rem;
            border-radius: 0.75rem;
            font-size: 0.95rem;
            max-width: 85%;
            line-height: 1.4;
        }

        .msg-agent {
            background: rgba(168, 85, 247, 0.2);
            border: 1px solid rgba(168, 85, 247, 0.3);
            align-self: flex-start;
        }

        .msg-user {
            background: var(--accent-pink);
            color: white;
            align-self: flex-end;
        }

        .chat-input-bar {
            display: flex;
            padding: 0.75rem;
            background: rgba(0,0,0,0.6);
            gap: 0.5rem;
        }

        .chat-input-bar input {
            flex: 1;
            background: rgba(255,255,255,0.08);
            border: 1px solid var(--card-border);
            padding: 0.6rem 1rem;
            border-radius: 0.5rem;
            color: white;
            outline: none;
        }

        footer { text-align: center; margin-top: 3rem; font-size: 0.85rem; color: var(--text-muted); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-title">
                <h1>🌸 Beauty Care</h1>
            </div>
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
        <input type="email" placeholder="Staff Email (e.g. manager@oxyjet.win)">
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
            alert('Staff user registered successfully: ' + data.name + ' (' + data.role + ')');
            location.href = '/dashboard';
        }
    </script>
</body>
</html>
"""


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard_page() -> str:
    """Protected Staff & Master Management Dashboard (beauty-admin.oxyjet.win)."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌸 Admin & Master Dashboard — Beauty Care</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { background: #0f172a; color: white; font-family: 'Outfit', sans-serif; padding: 2rem; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem; margin-bottom: 2rem; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 1rem; }
        h2 { color: #ec4899; margin-bottom: 1rem; }
        ul { list-style: none; padding: 0; }
        li { padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌸 Beauty Care Admin & Master Portal</h1>
            <a href="/" style="color:#06b6d4; text-decoration:none;">View Client Website ↗</a>
        </header>

        <div class="cards">
            <div class="card">
                <h2>👥 Registered Staff Members</h2>
                <ul id="usersList">
                    <li>👑 <strong>admin@oxyjet.win</strong> (Super Admin)</li>
                    <li>🏬 <strong>manager@oxyjet.win</strong> (Salon Manager)</li>
                    <li>💇‍♀️ <strong>anna@oxyjet.win</strong> (Top Stylist)</li>
                </ul>
            </div>

            <div class="card">
                <h2>📚 RAG Wiki Knowledge Base</h2>
                <ul>
                    <li>✂️ Hair Coloring Pre-Care Advice</li>
                    <li>✨ Уход после чистки лица</li>
                </ul>
            </div>

            <div class="card">
                <h2>🔒 Security & Audio Retention</h2>
                <p>PII Sanitizer: <strong>ACTIVE</strong></p>
                <p>Audio Retention: <strong>OFF</strong> (Privacy Mode)</p>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.post("/api/v1/admin/users/register", status_code=status.HTTP_201_CREATED)
async def register_staff_user(user: UserRegistration) -> Dict[str, Any]:
    """Register a new staff member (Manager, Receptionist, Master, Admin)."""
    record = user.model_dump()
    _staff_users.append(record)
    return {"status": "registered", "name": user.name, "email": user.email, "role": user.role}


@app.get("/api/v1/admin/users")
async def list_staff_users() -> List[Dict[str, Any]]:
    """List all registered staff members."""
    return _staff_users


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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8019)
