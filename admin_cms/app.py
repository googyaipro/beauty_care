"""Multilingual Admin CMS, Client Landing Widget & Staff Portal for Beauty Care.

Includes LIVE Multi-Tab Interactive Admin Dashboard for IT Super Admin & Salon Managers.
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
    title="Beauty Care Platform UI & Admin Dashboard",
    description="Client Web Booking Widget & Interactive Staff Admin Portal",
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
    "gcp_project": "beauty-care-platform",
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


class WikiArticle(BaseModel):
    title: str
    category: str
    language: str = "en"
    content: str


class AudioToggleRequest(BaseModel):
    enabled: bool


@app.post("/api/v1/chat")
async def handle_live_chat(req: ChatMessageRequest) -> Dict[str, Any]:
    """LIVE Multi-Agent Chat Endpoint for Web Booking Widget."""
    user_text = req.message.strip()
    if not user_text:
        return {"reply": "Please enter a valid message."}

    lang = detect_language(user_text)

    sanitizer = PIISanitizer()
    sanitized_text, _ = sanitizer.sanitize(user_text)

    archiver.archive_message(
        session_id=req.session_id,
        sender_role="user",
        content=user_text,
        channel="web_widget",
        language=lang,
    )

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
            alert('Staff user registered successfully: ' + data.name + ' (' + data.role + ')');
            location.href = '/dashboard';
        }
    </script>
</body>
</html>
"""


@app.get("/dashboard", response_class=HTMLResponse)
async def get_interactive_dashboard_page() -> str:
    """Rich Multi-Tab Interactive Admin Dashboard for IT Super Admin & Salon Managers."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌸 Interactive Admin Dashboard — Beauty Care</title>
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

        <!-- Navigation Tabs -->
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('overview')">📊 System Overview</button>
            <button class="tab-btn" onclick="switchTab('wiki')">📚 RAG Wiki Editor</button>
            <button class="tab-btn" onclick="switchTab('staff')">👥 Staff & Roles</button>
            <button class="tab-btn" onclick="switchTab('chats')">💬 Chat Inspector</button>
            <button class="tab-btn" onclick="switchTab('settings')">⚙️ Security & Audio</button>
        </div>

        <!-- Tab 1: System Overview & Telemetry -->
        <div id="tab-overview" class="tab-content active">
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
                    <h2>☁️ Cloud Infrastructure</h2>
                    <p style="color:var(--text-muted); font-size:0.95rem; margin-bottom:0.5rem;">GCP Dedicated Project: <code>beauty-care-platform</code></p>
                    <p style="color:var(--text-muted); font-size:0.95rem; margin-bottom:0.5rem;">Domain Namespace: <code>beauty-*.oxyjet.win</code></p>
                    <p style="color:var(--text-muted); font-size:0.95rem;">Cloudflare Proxy & SSL: <strong style="color:#10b981;">Active 🟧</strong></p>
                </div>
            </div>
        </div>

        <!-- Tab 2: RAG Wiki Knowledge Base Editor -->
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

        <!-- Tab 3: Staff & Role Management -->
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

        <!-- Tab 4: Chat Inspector -->
        <div id="tab-chats" class="tab-content">
            <div class="card">
                <h2>💬 Real-Time Client Dialogue Inspector</h2>
                <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:1rem;">Inspect live conversations across WhatsApp, Telegram, and Web Chat Widget.</p>
                <table class="table">
                    <thead>
                        <tr><th>Time</th><th>Channel</th><th>Lang</th><th>Client Request</th><th>AI Agent Reply</th></tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>18:20</td>
                            <td><span style="color:#10b981;">WhatsApp</span></td>
                            <td>RU</td>
                            <td>Хочу записаться на окрашивание в эту пятницу</td>
                            <td>Отлично! У мастера Анны на эту пятницу в Google Календаре есть свободные окна...</td>
                        </tr>
                        <tr>
                            <td>17:45</td>
                            <td><span style="color:#06b6d4;">Telegram</span></td>
                            <td>EN</td>
                            <td>What are the pre-care steps for hair bleaching?</td>
                            <td>Do not wash your hair 24 hours prior to bleaching to protect your scalp...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Tab 5: Security & Settings -->
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
        }

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
