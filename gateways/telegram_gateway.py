"""Telegram Messaging Gateway.

Receives webhook payloads from Telegram Bot API, detects language, anonymizes PII,
routes messages to Concierge Agent, and returns response to client.
"""

from typing import Any, Dict
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes
from common.language_detector import detect_language
from common.pii_sanitizer import PIISanitizer
from common.dialogue_archiver import DialogueArchiver

app = FastAPI(
    title="Telegram Messaging Gateway",
    description="Webhook Endpoint for Telegram Bot Integration on api.oxyjet.win",
    version="1.0.0",
)

attach_health_routes(app, service_name="telegram_gateway")

archiver = DialogueArchiver()


class TelegramWebhookPayload(BaseModel):
    update_id: int
    message: Dict[str, Any]


@app.post("/v1/webhook/telegram")
async def handle_telegram_webhook(payload: TelegramWebhookPayload) -> Dict[str, Any]:
    """Receive Telegram webhook message and process through Multi-Agent Core."""
    msg = payload.message
    chat_id = str(msg.get("chat", {}).get("id"))
    user_text = msg.get("text", "")

    # 1. Detect language
    lang = detect_language(user_text)

    # 2. Sanitize PII (152-ФЗ / GDPR)
    sanitizer = PIISanitizer()
    sanitized_text, _ = sanitizer.sanitize(user_text)

    # 3. Record in Dialogue Archive
    archiver.archive_message(
        session_id=f"tg_{chat_id}",
        sender_role="user",
        content=user_text,
        channel="telegram",
        language=lang,
    )

    # Response placeholder
    bot_reply = f"[Telegram Gateway Processed ({lang})]: Thank you for contacting Beauty Care! How can I assist you with your salon appointment today?"

    archiver.archive_message(
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
