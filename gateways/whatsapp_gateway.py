"""WhatsApp Business Messaging Gateway.

Receives webhook payloads from WhatsApp Business API / GreenAPI on api.oxyjet.win.
"""

from typing import Any, Dict
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes
from common.language_detector import detect_language
from common.pii_sanitizer import PIISanitizer
from common.dialogue_archiver import DialogueArchiver

app = FastAPI(
    title="WhatsApp Business Gateway",
    description="Webhook Endpoint for WhatsApp Business Integration on api.oxyjet.win",
    version="1.0.0",
)

attach_health_routes(app, service_name="whatsapp_gateway")

archiver = DialogueArchiver()


class WhatsAppWebhookPayload(BaseModel):
    phone_number: str
    message_text: str


@app.post("/v1/webhook/whatsapp")
async def handle_whatsapp_webhook(payload: WhatsAppWebhookPayload) -> Dict[str, Any]:
    """Receive WhatsApp webhook message and process through Multi-Agent Core."""
    lang = detect_language(payload.message_text)

    sanitizer = PIISanitizer()
    sanitized_text, _ = sanitizer.sanitize(payload.message_text)

    archiver.archive_message(
        session_id=f"wa_{payload.phone_number}",
        sender_role="user",
        content=payload.message_text,
        channel="whatsapp",
        language=lang,
    )

    bot_reply = f"[WhatsApp Gateway Processed ({lang})]: Hello! Welcome to Beauty Care. How can we help you today?"

    archiver.archive_message(
        session_id=f"wa_{payload.phone_number}",
        sender_role="agent",
        content=bot_reply,
        channel="whatsapp",
        language=lang,
    )

    return {
        "status": "ok",
        "phone_number": payload.phone_number,
        "language_detected": lang,
        "reply": bot_reply,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8022)
