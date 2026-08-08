import os
import sys

# Ensure /app root directory is in sys.path for common.* imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/app")

import uuid
import httpx
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes
from common.language_detector import detect_language
from common.pii_sanitizer import PIISanitizer
from common.dialogue_store import SharedDialogueStore
from common.rate_limiter import check_rate_limit
from common.orchestrator import generate_dynamic_agent_response

app = FastAPI(
    title="Telegram & WhatsApp Gateway",
    description="Webhook Endpoint for Messaging Integration on beauty-api.oxyjet.win",
    version="1.0.0",
)

attach_health_routes(app, service_name="telegram_gateway")


class WhatsAppWebhookPayload(BaseModel):
    phone_number: str
    message_text: str


async def _send_telegram_api_message(chat_id: str, text: str, buttons: list):
    """Send message back to user via Telegram Bot HTTP API."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("[Telegram Gateway Error] TELEGRAM_BOT_TOKEN environment variable is not set!")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if buttons:
        keyboard = []
        for btn in buttons:
            keyboard.append([{"text": btn.title, "callback_data": btn.action_payload or btn.title}])
        payload["reply_markup"] = {"inline_keyboard": keyboard}

    print(f"[Telegram Outbound] Sending to chat_id={chat_id} using token={token[:10]}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10.0)
            print(f"[Telegram Outbound Result] Status: {resp.status_code}, Body: {resp.text}")
    except Exception as exc:
        print(f"[Telegram Outbound Exception] Error sending message to chat {chat_id}: {exc}")


@app.post("/v1/webhook/whatsapp")
async def handle_whatsapp_webhook(payload: WhatsAppWebhookPayload) -> Dict[str, Any]:
    """Receive WhatsApp webhook payload with dynamic CRM & Maps MCP resolution."""
    check_rate_limit(f"wa_{payload.phone_number}")
    trace_id = str(uuid.uuid4())

    user_text = payload.message_text.strip()
    lang = detect_language(user_text)

    sanitizer = PIISanitizer()
    sanitized_text, _ = sanitizer.sanitize(user_text)

    session_id = f"wa_{payload.phone_number}"

    SharedDialogueStore.add_message(
        session_id=session_id,
        sender_role="user",
        content=user_text,
        channel="whatsapp",
        language=lang,
    )

    structured_msg = await generate_dynamic_agent_response(
        user_text=user_text,
        lang=lang,
        session_id=session_id,
        trace_id=trace_id,
    )

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
async def handle_telegram_webhook(request: Request) -> Dict[str, Any]:
    """Receive Telegram webhook payload with dynamic CRM & Maps MCP resolution."""
    try:
        body = await request.json()
    except Exception as exc:
        print(f"[Telegram Webhook Error] Invalid JSON payload: {exc}")
        return {"status": "error", "reason": "invalid_json"}

    print(f"[Telegram Webhook Incoming] Payload: {body}")

    msg = body.get("message") or body.get("edited_message") or {}
    callback_query = body.get("callback_query")

    if callback_query:
        chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id") or callback_query.get("from", {}).get("id", ""))
        user_text = callback_query.get("data", "")
    else:
        chat_id = str(msg.get("chat", {}).get("id", ""))
        user_text = msg.get("text", "")

    if not chat_id or not user_text:
        print(f"[Telegram Webhook Ignored] missing chat_id ({chat_id}) or text ({user_text})")
        return {"status": "ignored", "reason": "missing_chat_id_or_text"}

    try:
        check_rate_limit(f"tg_{chat_id}")
    except Exception as exc:
        print(f"[Telegram Rate Limit Warning] {exc}")

    trace_id = str(uuid.uuid4())
    lang = detect_language(user_text)

    sanitizer = PIISanitizer()
    sanitized_text, _ = sanitizer.sanitize(user_text)

    session_id = f"tg_{chat_id}"

    SharedDialogueStore.add_message(
        session_id=session_id,
        sender_role="user",
        content=user_text,
        channel="telegram",
        language=lang,
    )

    try:
        structured_msg = await generate_dynamic_agent_response(
            user_text=user_text,
            lang=lang,
            session_id=session_id,
            trace_id=trace_id,
        )
    except Exception as exc:
        print(f"[Telegram Orchestrator Error] {exc}")
        # Send emergency fallback response to user
        await _send_telegram_api_message(
            chat_id=chat_id,
            text="🌸 Извините, произошел временный сбой. Напишите нам еще раз!",
            buttons=[],
        )
        return {"status": "error", "detail": str(exc)}

    SharedDialogueStore.add_message(
        session_id=session_id,
        sender_role="agent",
        content=structured_msg.text_response,
        channel="telegram",
        language=lang,
    )

    # Dispatch directly via Telegram API
    await _send_telegram_api_message(
        chat_id=chat_id,
        text=structured_msg.text_response,
        buttons=structured_msg.buttons,
    )

    return {"status": "ok", "chat_id": chat_id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8021)
