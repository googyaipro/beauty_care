"""Telegram & WhatsApp Gateway Router.

Handles both Telegram and WhatsApp webhooks with REAL DYNAMIC HTTP queries to
Google Calendar CRM MCP and Google Maps MCP via common.orchestrator.
"""

import uuid
from typing import Any, Dict
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes
from common.language_detector import detect_language
from common.pii_sanitizer import PIISanitizer
from common.dialogue_store import SharedDialogueStore
from common.rate_limiter import check_rate_limit
from common.telemetry import trace_step
from common.orchestrator import generate_dynamic_agent_response

app = FastAPI(
    title="Telegram & WhatsApp Gateway",
    description="Webhook Endpoint for Messaging Integration on beauty-api.oxyjet.win",
    version="1.0.0",
)

attach_health_routes(app, service_name="telegram_gateway")


class TelegramWebhookPayload(BaseModel):
    update_id: int = 1
    message: Dict[str, Any]


class WhatsAppWebhookPayload(BaseModel):
    phone_number: str
    message_text: str


@app.post("/v1/webhook/whatsapp")
async def handle_whatsapp_webhook(payload: WhatsAppWebhookPayload) -> Dict[str, Any]:
    """Receive WhatsApp webhook payload with dynamic CRM & Maps MCP resolution."""
    check_rate_limit(f"wa_{payload.phone_number}")
    trace_id = str(uuid.uuid4())

    with trace_step(trace_id, "WhatsApp_Webhook"):
        user_text = payload.message_text.strip()
        lang = detect_language(user_text)

        sanitizer = PIISanitizer()
        sanitized_text, _ = sanitizer.sanitize(user_text)

        session_id = f"wa_{payload.phone_number}"

        # Save incoming user message
        SharedDialogueStore.add_message(
            session_id=session_id,
            sender_role="user",
            content=user_text,
            channel="whatsapp",
            language=lang,
        )

        # Generate REAL DYNAMIC response via Google Calendar CRM & Maps MCP
        structured_msg = await generate_dynamic_agent_response(
            user_text=user_text,
            lang=lang,
            session_id=session_id,
            trace_id=trace_id,
        )

        # Save dynamic agent response
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
    """Receive Telegram webhook payload with dynamic CRM & Maps MCP resolution."""
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

        # Save user message
        SharedDialogueStore.add_message(
            session_id=session_id,
            sender_role="user",
            content=user_text,
            channel="telegram",
            language=lang,
        )

        # Generate REAL DYNAMIC response via Google Calendar CRM & Maps MCP
        structured_msg = await generate_dynamic_agent_response(
            user_text=user_text,
            lang=lang,
            session_id=session_id,
            trace_id=trace_id,
        )

        # Save dynamic agent response
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8021)
