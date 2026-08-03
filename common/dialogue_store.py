"""Shared Dialogue Store & Persistence Engine for Beauty Care Platform.

Persists all dialogue messages (Telegram, WhatsApp, Web Widget, curl tests) to a shared file database
so that Admin CMS Chat Inspector displays all real-time client interactions across all gateways.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DIALOGUES_FILE = DATA_DIR / "dialogues_store.json"
SETTINGS_FILE = DATA_DIR / "settings_store.json"
USERS_FILE = DATA_DIR / "users_store.json"
WIKI_FILE = DATA_DIR / "wiki_store.json"


def _read_json(file_path: Path, default_data: Any) -> Any:
    if not file_path.exists():
        return default_data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_data


def _write_json(file_path: Path, data: Any) -> None:
    try:
        temp_file = file_path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        temp_file.replace(file_path)
    except Exception as exc:
        print(f"Error writing file {file_path}: {exc}")


class SharedDialogueStore:

    @staticmethod
    def add_message(
        session_id: str,
        sender_role: str,
        content: str,
        channel: str = "web_widget",
        language: str = "en",
        audio_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record message to shared persistent store."""
        dialogues = _read_json(DIALOGUES_FILE, [])
        
        entry = {
            "id": len(dialogues) + 1,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "full_timestamp": datetime.now(timezone.utc).isoformat(),
            "sender_role": sender_role,
            "content": content,
            "channel": channel,
            "language": language.upper(),
            "audio_file": audio_file,
        }
        
        dialogues.append(entry)
        _write_json(DIALOGUES_FILE, dialogues)
        return entry

    @staticmethod
    def get_all_messages(limit: int = 100) -> List[Dict[str, Any]]:
        """Get all recorded messages across all channels."""
        dialogues = _read_json(DIALOGUES_FILE, [])
        return dialogues[-limit:]


class SharedSettingsStore:

    @staticmethod
    def get_settings() -> Dict[str, Any]:
        default_settings = {
            "save_audio_recordings": False,
            "primary_language": "en",
            "supported_languages": ["en", "ru", "ka", "de", "it", "es", "fr"],
            "payment_provider": "stripe",
            "gcp_project": "beauty-care-platform",
        }
        return _read_json(SETTINGS_FILE, default_settings)

    @staticmethod
    def update_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
        current = SharedSettingsStore.get_settings()
        current.update(updates)
        _write_json(SETTINGS_FILE, current)
        return current


class SharedUserStore:

    @staticmethod
    def get_users() -> List[Dict[str, Any]]:
        default_users = [
            {"email": "admin@oxyjet.win", "name": "Super Admin", "role": "super_admin"},
            {"email": "manager@oxyjet.win", "name": "Elena Manager", "role": "salon_manager"},
            {"email": "anna@oxyjet.win", "name": "Anna Stylist", "role": "master"},
        ]
        return _read_json(USERS_FILE, default_users)

    @staticmethod
    def add_user(name: str, email: str, role: str) -> Dict[str, Any]:
        users = SharedUserStore.get_users()
        user = {"email": email, "name": name, "role": role}
        users.append(user)
        _write_json(USERS_FILE, users)
        return user


class SharedWikiStore:

    @staticmethod
    def get_articles() -> List[Dict[str, Any]]:
        default_articles = [
            {
                "id": "wiki_1",
                "title": "Hair Coloring Pre-Care Advice",
                "category": "hair",
                "language": "EN",
                "content": "Do not wash your hair 24 hours prior to bleaching or complex coloring to protect your scalp.",
            },
            {
                "id": "wiki_2",
                "title": "Уход после чистки лица",
                "category": "cosmetology",
                "language": "RU",
                "content": "Избегайте посещения сауны, солярия и интенсивных тренировок в течение 48 часов после глубокой чистки лица.",
            },
        ]
        return _read_json(WIKI_FILE, default_articles)

    @staticmethod
    def add_article(title: str, category: str, language: str, content: str) -> Dict[str, Any]:
        articles = SharedWikiStore.get_articles()
        article = {
            "id": f"wiki_{len(articles) + 1}",
            "title": title,
            "category": category,
            "language": language.upper(),
            "content": content,
        }
        articles.append(article)
        _write_json(WIKI_FILE, articles)
        return article
