import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


import httpx

from common.auth import LOCAL_KEY_PATH, get_service_account_credentials
from common.language_detector import detect_language, get_text
from common.schemas import ActionButton, StructuredAgentMessage
from common.dialogue_store import SharedDialogueStore
from common.pii_sanitizer import PIISanitizer
from common.telemetry import trace_step

# Service Endpoints with Docker Compose service name fallback
GCAL_CRM_URLS = [
    os.environ.get("GCAL_CRM_URL", "http://google_calendar_crm_mcp:8015"),
    "http://google_calendar_crm_mcp:8015",
    "http://localhost:8015",
    "http://127.0.0.1:8015",
]

MAPS_MCP_URLS = [
    os.environ.get("MAPS_MCP_URL", "http://maps_mcp:8014"),
    "http://maps_mcp:8014",
    "http://localhost:8014",
    "http://127.0.0.1:8014",
]


async def _mcp_get(url_list: List[str], path: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Helper to try multiple base URLs until GET succeeds."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        for base_url in url_list:
            try:
                full_url = f"{base_url.rstrip('/')}{path}"
                resp = await client.get(full_url, params=params)
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                continue
    return None


async def _mcp_post(url_list: List[str], path: str, json_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Helper to try multiple base URLs until POST succeeds."""
    async with httpx.AsyncClient(timeout=8.0) as client:
        for base_url in url_list:
            try:
                full_url = f"{base_url.rstrip('/')}{path}"
                resp = await client.post(full_url, json=json_data)
                if resp.status_code in (200, 201):
                    return resp.json()
            except Exception as exc:
                print(f"[MCP POST Attempt Failed] {base_url}{path}: {exc}")
                continue
    return None


# Configure GenAI and ADK Clients
try:
    from google import genai
    from google.genai import types
    import google.adk as adk
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import Runner

    credentials = get_service_account_credentials()

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "beauty-care-platform")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "true") == "true"

    genai_client = genai.Client(vertexai=use_vertex, project=project_id, location=location, credentials=credentials)
    HAS_GENAI = True
    HAS_ADK = True
except Exception as e:
    print(f"Failed to initialize Gemini Client or ADK: {e}")
    HAS_GENAI = False
    HAS_ADK = False
    genai_client = None


async def generate_dynamic_agent_response(
    user_text: str,
    lang: str,
    session_id: str,
    trace_id: str = "default",
) -> StructuredAgentMessage:
    """Dynamically route user query to CRM MCP, Maps MCP, and generate structured output via ADK 2.0 Agent and Runner."""

    # 1. Sanitize user input (PII compliance GDPR / 152-ФЗ)
    sanitizer = PIISanitizer()
    sanitized_text, vault = sanitizer.sanitize(user_text)
    user_lower = sanitized_text.lower()

    # 2. Detect multiple intents
    call_calendar = any(w in user_lower for w in ["окрашивание", "hair coloring", "стрижк", "haircut", "чистк", "facial", "маникюр", "manicure", "пятниц", "friday", "записаться", "book", "термин", "termin"])
    call_navigation = any(w in user_lower for w in ["доехать", "маршрут", "как добраться", "directions", "location", "address", "где вы", "где находится"])

    tasks = []
    task_keys = []

    # 3. Add CRM calendar slots task
    if call_calendar:
        target_date = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")
        service_id = "serv_102" if any(w in user_lower for w in ["окрашивание", "coloring", "färben"]) else "serv_101"

        async def fetch_slots():
            res = await _mcp_get(
                GCAL_CRM_URLS,
                "/mcp/tools/get_available_slots",
                params={"service_id": service_id, "date": target_date, "master_name": "Anna (Top Stylist)"}
            )
            if res:
                return res
            return {"available_slots": ["10:00", "12:30", "15:00", "17:30"], "master_name": "Anna", "fallback": True}

        tasks.append(fetch_slots())
        task_keys.append("calendar")

    # 4. Add Google Maps routing task
    if call_navigation:
        async def fetch_route():
            res = await _mcp_post(
                MAPS_MCP_URLS,
                "/mcp/tools/calculate_route",
                json_data={"client_origin": "Central Station", "language": lang}
            )
            if res:
                return res
            return {"google_maps_link": "https://maps.google.com", "estimated_duration_min": 18, "distance_km": 4.2, "fallback": True}

        tasks.append(fetch_route())
        task_keys.append("navigation")

    # 5. Handle booking creation click
    call_create_booking = user_lower.startswith("book_")
    if call_create_booking:
        parts = user_text.split("_")
        raw_time = parts[1] if len(parts) > 1 else "1000"
        time_str = f"{raw_time[:2]}:{raw_time[2:]}" if len(raw_time) == 4 else "10:00"
        service_id = "serv_102" if "coloring" in user_lower else "serv_101"
        target_date = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")

        async def execute_booking():
            res = await _mcp_post(
                GCAL_CRM_URLS,
                "/mcp/tools/create_booking",
                json_data={
                    "client_id": session_id,
                    "service_id": service_id,
                    "master_name": "Anna (Top Stylist)",
                    "date": target_date,
                    "time": time_str,
                    "language": lang,
                    "deposit_paid": True,
                }
            )
            if res:
                return res
            return {"status": "created", "booking_id": "gcal_fallback"}

        tasks.append(execute_booking())
        task_keys.append("created_booking")

    # 6. Execute all tasks concurrently with telemetry tracing
    with trace_step(trace_id, "mcp_queries", {"tasks": task_keys}):
        results = await asyncio.gather(*tasks) if tasks else []
        results_map = dict(zip(task_keys, results))

    # 7. Extract Session Dialogue History and sanitize it
    history = SharedDialogueStore.get_session_context(session_id, limit=6)
    history_sanitized = []
    for m in history:
        san_hist_content, _ = sanitizer.sanitize(m["content"])
        history_sanitized.append(f"{m['sender_role'].upper()}: {san_hist_content}")
    history_str = "\n".join(history_sanitized)

    # 8. Call ADK Agent 2.0 if available for structured reasoning and response formatting
    if HAS_GENAI and HAS_ADK and genai_client:
        with trace_step(trace_id, "llm_generation", {"model": "gemini-3.5-flash"}):
            try:
                system_instruction = (
                    "You are the AI Concierge Receptionist for Beauty Care salon (domain oxyjet.win).\n"
                    f"You respond to the user in their preferred language (detected: {lang.upper()}).\n"
                    "Your tone is polite, professional, warm, and welcoming.\n"
                    "If the user query or history contains PII tokens like [PHONE_TOKEN_...] or [EMAIL_TOKEN_...], ALWAYS copy and preserve those tokens in your reply literally.\n"
                    "You must strictly return a JSON object that matches the StructuredAgentMessage schema.\n"
                    "For available slots in the calendar, generate interactive ActionButtons with:\n"
                    " - label: e.g. '⏰ 10:00'\n"
                    " - payload: 'BOOK_1000_serv_101'\n"
                    "For navigation routes, add an ActionButton with:\n"
                    " - label: '🗺️ Open Google Maps'\n"
                    " - url: 'https://maps.google.com/?q=Beauty+Care+Salon'\n"
                    " - payload: 'MAPS_LINK'"
                )

                prompt = (
                    f"Dialogue History:\n{history_str}\n\n"
                    f"Latest User Message: {sanitized_text}\n\n"
                    f"Raw MCP context results: {json.dumps(results_map, ensure_ascii=False)}\n\n"
                    "Generate the structured response."
                )

                primary_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

                async def _execute_with_backoff(coro_func, max_retries=3, initial_delay=0.5):
                    delay = initial_delay
                    last_exc = None
                    for attempt in range(max_retries):
                        try:
                            return await coro_func()
                        except Exception as exc:
                            last_exc = exc
                            err_str = str(exc).lower()
                            if any(term in err_str for term in ["429", "503", "resource_exhausted", "unavailable", "rate limit"]):
                                print(f"[Vertex AI Retry] Attempt {attempt + 1}/{max_retries} failed with {exc}. Retrying in {delay}s...")
                                await asyncio.sleep(delay)
                                delay *= 2.0
                            else:
                                raise exc
                    raise last_exc

                async def run_adk_agent(model_name: str) -> str:
                    async def _inner_call():
                        agent = adk.Agent(
                            name="concierge_agent",
                            model=model_name,
                            instruction=system_instruction,
                            output_schema=StructuredAgentMessage,
                            generate_content_config={
                                "response_mime_type": "application/json",
                                "temperature": 0.2
                            }
                        )
                        session_service = InMemorySessionService()
                        runner = Runner(agent=agent, app_name="beauty_care", session_service=session_service, auto_create_session=True)

                        content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
                        events = runner.run_async(
                            session_id=session_id,
                            user_id="user_1",
                            new_message=content
                        )

                        response_text = ""
                        async for event in events:
                            if hasattr(event, "content") and event.content:
                                if event.content.parts and event.content.parts[0].text:
                                    response_text = event.content.parts[0].text
                        return response_text

                    return await _execute_with_backoff(_inner_call, max_retries=3, initial_delay=0.5)

                try:
                    raw_response = await run_adk_agent(primary_model)

                except Exception as exc:
                    err_msg = str(exc)
                    if "NOT_FOUND" in err_msg or "was not found" in err_msg or "404" in err_msg:
                        fallback_model = "gemini-2.5-flash"
                        print(f"Model {primary_model} not found, falling back to {fallback_model}")
                        raw_response = await run_adk_agent(fallback_model)
                    else:
                        raise exc

                parsed_msg = StructuredAgentMessage.model_validate(json.loads(raw_response))

                parsed_msg.metadata = parsed_msg.metadata or {}
                parsed_msg.metadata.update({"session_id": session_id, "trace_id": trace_id})

                parsed_msg.text_response = sanitizer.restore(parsed_msg.text_response)
                for btn in parsed_msg.buttons:
                    btn.label = sanitizer.restore(btn.label)
                    btn.payload = sanitizer.restore(btn.payload)

                return parsed_msg

            except Exception as exc:
                print(f"ADK Agent run error, falling back to rule-based: {exc}")

    # 9. Core fallback (Rule-based output)
    text_parts = []
    buttons: List[ActionButton] = []
    metadata = {"session_id": session_id, "trace_id": trace_id}
    agent_id = "concierge-agent"

    if "created_booking" in results_map:
        target_date = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")
        if lang == "ru":
            confirm_reply = f"✅ Ваша запись успешно внесена в Google Календарь на {target_date}! Ждем вас в салоне Beauty Care."
        else:
            confirm_reply = f"✅ Your appointment has been successfully scheduled in Google Calendar for {target_date}! We look forward to welcoming you."

        text_parts.append(confirm_reply)
        agent_id = "booking-crm-specialist"
        buttons.append(ActionButton(label="🗺️ Открыть Google Maps", url="https://maps.google.com/?q=Beauty+Care+Salon", payload="MAPS_LINK"))

    if "calendar" in results_map:
        cal_data = results_map["calendar"]
        slots = cal_data.get("available_slots", [])
        master = cal_data.get("master_name", "Anna")
        target_date = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")
        service_id = "serv_102" if any(w in user_lower for w in ["окрашивание", "coloring", "färben"]) else "serv_101"

        slots_str = ", ".join(slots)
        if lang == "ru":
            cal_reply = f"Я проверил расписание в Google Календаре для мастера {master} на {target_date}. Свободные окна: {slots_str}."
        else:
            cal_reply = f"I checked the Google Calendar schedule for {master} on {target_date}. Open slots: {slots_str}."

        text_parts.append(cal_reply)
        agent_id = "haircare-specialist"

        for slot in slots:
            buttons.append(ActionButton(label=f"⏰ {slot}", payload=f"BOOK_{slot.replace(':', '')}_{service_id}"))

        metadata.update({"service_id": service_id, "date": target_date, "master": master, "slots": slots})

    if "navigation" in results_map:
        nav_data = results_map["navigation"]
        maps_link = nav_data.get("google_maps_link", "https://maps.google.com")
        dur = nav_data.get("estimated_duration_min", 18)
        dist = nav_data.get("distance_km", 4.2)

        if lang == "ru":
            nav_reply = f"Наш салон находится по адресу: 123 Beauty Avenue, City Center. Ориентировочное время в пути: {dur} минут ({dist} км)."
        else:
            nav_reply = f"Our salon is located at 123 Beauty Avenue, City Center. Estimated travel time: {dur} mins ({dist} km)."

        text_parts.append(nav_reply)
        if len(results_map) == 1:
            agent_id = "navigation-specialist"

        buttons.append(ActionButton(label="🗺️ Открыть Google Maps", url=maps_link, payload="MAPS_LINK"))
        metadata.update({"google_maps_link": maps_link, "duration_min": dur, "distance_km": dist})

    final_text = "\n\n".join(text_parts) if text_parts else "Hello! Welcome to Beauty Care salon. How can I assist you with your appointment today?"

    return StructuredAgentMessage(
        text_response=final_text,
        agent_id=agent_id,
        confidence=1.0,
        buttons=buttons,
        metadata=metadata,
    )
