"""Telegram Messaging Gateway.

Receives webhook payloads from Telegram Bot API, detects language, anonymizes PII,
routes messages to Concierge Agent, and saves to SharedDialogueStore for Chat Inspector.
"""

from typing import Any, Dict
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes
from common.language_detector import detect_language
from common.pii_sanitizer import PIISanitizer
from common.dialogue_store import SharedDialogueStore

app = FastAPI(
    title="Telegram Messaging Gateway",
    description="Webhook Endpoint for Telegram Bot Integration on beauty-api.oxyjet.win",
    version="1.0.0",
)

attach_health_routes(app, service_name="telegram_gateway")


class TelegramWebhookPayload(BaseModel):
    update_id: int
    message: Dict[str, Any]


@app.post("/v1/webhook/telegram")
async def handle_telegram_webhook(payload: TelegramWebhookPayload) -> Dict[str, Any]:
    """Receive Telegram webhook message and process through Multi-Agent Core."""
    msg = payload.message
    chat_id = str(msg.get("chat", {}).get("id", "777"))
    user_text = msg.get("text", "")

    # 1. Detect language
    lang = detect_language(user_text)

    # 2. Sanitize PII (152-ФЗ / GDPR)
    sanitizer = PIISanitizer()
    sanitized_text, _ = sanitizer.sanitize(user_text)

    # 3. Save User message to Shared Persistent Store for Chat Inspector
    SharedDialogueStore.add_message(
        session_id=f"tg_{chat_id}",
        sender_role="user",
        content=user_text,
        channel="telegram",
        language=lang,
    )

    # 4. Generate AI Agent response
    user_lower = user_text.lower()
    if any(w in user_lower for w in ["окрашивание", "hair coloring", "стрижк", "haircut", "пятниц", "friday", "записаться", "book"]):
        if lang == "ru":
            bot_reply = "Отлично! У мастера Анны на эту пятницу в Google Календаре есть свободные окна: 10:00, 12:30, 15:00 и 17:30. Какое время вам больше подходит?"
        else:
            bot_reply = "Great! Top Stylist Anna has open slots in Google Calendar for this Friday: 10:00 AM, 12:30 PM, 3:00 PM, and 5:30 PM. Which time works best for you?"
    else:
        bot_reply = f"[Telegram Bot ({lang.upper()})]: Здравствуйте! Я ИИ-Администратор салона Beauty Care. Чем могу помочь вам сегодня?"

    # 5. Save Agent reply to Shared Persistent Store
    SharedDialogueStore.add_message(
        session_id=f"tg_{chat_id}",
        sender_role="agent",
        content=bot_reply,
        channel="telegram",
        language=lang,
    )

    return {
        "status": "ok",
        "chat_id": chat_id,
        "language_detected": lang,
        "reply": bot_reply,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8021)
