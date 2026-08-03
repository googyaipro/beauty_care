"""Unit tests for Beauty Care core modules."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.language_detector import detect_language, get_text
from common.pii_sanitizer import PIISanitizer
from common.dialogue_archiver import DialogueArchiver
from common.rbac import Role, Permission, has_permission


def test_language_detection() -> None:
    assert detect_language("Hello, I would like to book an appointment") == "en"
    assert detect_language("Здравствуйте, я хочу записаться на стрижку") == "ru"
    assert detect_language("გამარჯობა, მინდა ჩაწერა სალონში") == "ka"
    assert detect_language("Guten Tag, ich möchte einen Termin buchen") == "de"
    assert detect_language("Ciao, vorrei prenotare un appuntamento") == "it"
    assert detect_language("Hola, me gustaría reservar una cita") == "es"
    assert detect_language("Bonjour, je voudrais réserver un rendez-vous") == "fr"


def test_localization_strings() -> None:
    en_msg = get_text("en", "welcome_message")
    assert "Beauty Care" in en_msg

    ru_msg = get_text("ru", "appointment_details", date="05.08.2026", time="15:00", service="Стрижка", master="Анна", address="ул. Пушкина 10")
    assert "05.08.2026" in ru_msg
    assert "Стрижка" in ru_msg


def test_pii_sanitizer() -> None:
    sanitizer = PIISanitizer()
    raw_prompt = "Здравствуйте! Меня зовут Анна, мой телефон +7 (999) 123-45-67, email client@beauty.com"

    sanitized, vault = sanitizer.sanitize(raw_prompt)
    assert "+7 (999) 123-45-67" not in sanitized
    assert "client@beauty.com" not in sanitized
    assert "[PHONE_TOKEN_" in sanitized
    assert "[EMAIL_TOKEN_" in sanitized

    restored = sanitizer.restore(sanitized)
    assert restored == raw_prompt


def test_dialogue_archiver_audio_toggle(tmp_path: Path) -> None:
    archiver = DialogueArchiver(data_dir=tmp_path)
    assert archiver.save_audio_enabled is False

    # Create dummy audio file
    temp_audio = tmp_path / "temp_voice.ogg"
    temp_audio.write_bytes(b"OggS_dummy_audio_bytes")

    entry = archiver.archive_message(
        session_id="sess_101",
        sender_role="user",
        content="Testing voice message",
        audio_file_path=temp_audio,
    )

    # Audio should be deleted by default (save_audio_enabled = False)
    assert entry["audio_file"] is None
    assert not temp_audio.exists()


def test_rbac_permissions() -> None:
    assert has_permission(Role.SUPER_ADMIN, Permission.MANAGE_API_KEYS) is True
    assert has_permission(Role.SALON_MANAGER, Permission.MANAGE_RAG_WIKI) is True
    assert has_permission(Role.SALON_MANAGER, Permission.MANAGE_API_KEYS) is False
    assert has_permission(Role.MASTER, Permission.VIEW_PERSONAL_SCHEDULE) is True
    assert has_permission(Role.MASTER, Permission.MANAGE_RAG_WIKI) is False


if __name__ == "__main__":
    test_language_detection()
    test_localization_strings()
    test_pii_sanitizer()
    test_dialogue_archiver_audio_toggle(Path("/tmp"))
    test_rbac_permissions()
    print("All core tests passed successfully!")
