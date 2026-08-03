"""Language Detector & Localization Manager for Beauty Care Platform.

Supports 7 languages:
- en: English (Primary / Default)
- ru: Russian
- ka: Georgian (ქართული)
- de: German (Deutsch)
- it: Italian (Italiano)
- es: Spanish (Español)
- fr: French (Français)
"""

import json
import re
from pathlib import Path
from typing import Any, Dict

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ru": "Русский",
    "ka": "ქართული",
    "de": "Deutsch",
    "it": "Italiano",
    "es": "Español",
    "fr": "Français",
}

DEFAULT_LANGUAGE = "en"

_translations: Dict[str, Dict[str, str]] = {}


def load_translations() -> None:
    """Load all JSON locale files from the locales directory into memory."""
    global _translations
    for lang_code in SUPPORTED_LANGUAGES.keys():
        file_path = LOCALES_DIR / f"{lang_code}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                _translations[lang_code] = json.load(f)
        else:
            _translations[lang_code] = {}


# Load translations at module import time
load_translations()


def detect_language(text: str) -> str:
    """Detect text language using regex heuristics and character set rules.

    Falls back to 'en' if no specific script/keywords match.
    """
    if not text or not text.strip():
        return DEFAULT_LANGUAGE

    # Georgian script range: U+10A0 to U+10FF (Mkhedruli)
    if re.search(r"[\u10A0-\u10FF]", text):
        return "ka"

    # Cyrillic script range (Russian)
    if re.search(r"[\u0400-\u04FF]", text):
        return "ru"

    text_lower = text.lower()

    # German specific characters or common words
    if re.search(r"[äöüß]", text_lower) or any(w in text_lower for w in ["hallo", "guten tag", "termin", "buchen", "danke"]):
        return "de"

    # French specific characters or common words
    if re.search(r"[éèêëàâùûçœæ]", text_lower) or any(w in text_lower for w in ["bonjour", "salut", "rendez-vous", "merci"]):
        return "fr"

    # Spanish specific characters or common words
    if re.search(r"[ñáéíóú¿¡]", text_lower) or any(w in text_lower for w in ["hola", "gracias", "reserva", "cita", "buenos"]):
        return "es"

    # Italian specific common words
    if any(w in text_lower for w in ["ciao", "buongiorno", "prenotazione", "grazie", "appuntamento"]):
        return "it"

    return DEFAULT_LANGUAGE


def get_text(lang_code: str, key: str, **kwargs: Any) -> str:
    """Get localized string for key in given language, formatting with kwargs."""
    code = lang_code if lang_code in _translations else DEFAULT_LANGUAGE
    template = _translations.get(code, {}).get(key)
    if not template and code != DEFAULT_LANGUAGE:
        # Fallback to English if key missing in target language
        template = _translations.get(DEFAULT_LANGUAGE, {}).get(key, key)
    elif not template:
        template = key

    try:
        return template.format(**kwargs)
    except KeyError:
        return template
