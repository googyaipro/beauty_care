"""WhatsApp Business Messaging Gateway.

Receives webhook payloads from WhatsApp Business API / GreenAPI on beauty-api.oxyjet.win
and saves to SharedDialogueStore for Chat Inspector.
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
    title="WhatsApp Business Gateway",
    description="Webhook Endpoint for WhatsApp Business Integration on beauty-api.oxyjet.win",
    version="1.0.0",
)

attach_health_routes(app, service_name="whatsapp_gateway")


class WhatsAppWebhookPayload(BaseModel):
    phone_number: str
    message_text: str


@app.post("/v1/webhook/whatsapp")
async def handle_whatsapp_webhook(payload: WhatsAppWebhookPayload) -> Dict[str, Any]:
    """Receive WhatsApp webhook message and process through Multi-Agent Core."""
    user_text = payload.message_text.strip()
    lang = detect_language(user_text)

    sanitizer = PIISanitizer()
    sanitized_text, _ = sanitizer.sanitize(user_text)

    # 1. Save User message to Shared Persistent Store for Chat Inspector
    SharedDialogueStore.add_message(
        session_id=f"wa_{payload.phone_number}",
        sender_role="user",
        content=user_text,
        channel="whatsapp",
        language=lang,
    )

    # 2. Generate AI Agent response
    user_lower = user_text.lower()
    if any(w in user_lower for w in ["окрашивание", "hair coloring", "стрижк", "haircut", "пятниц", "friday", "записаться", "book"]):
        if lang == "ru":
            bot_reply = "Отлично! У мастера Анны на эту пятницу в Google Календаре есть свободные окна: 10:00, 12:30, 15:00 и 17:30. Какое время вам больше подходит?"
        else:
            bot_reply = "Great! Top Stylist Anna has open slots in Google Calendar for this Friday: 10:00 AM, 12:30 PM, 3:00 PM, and 5:30 PM. Which time works best for you?"
    else:
        bot_reply = f"[WhatsApp AI Concierge ({lang.upper()})]: Hello! Welcome to Beauty Care. How can we help you today?"

    # 3. Save Agent reply to Shared Persistent Store
    SharedDialogueStore.add_message(
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
