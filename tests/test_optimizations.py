"""Unit tests for the 6 architectural optimizations in Beauty Care platform."""

import unittest
import asyncio
from common.schemas import ActionButton, BookingResponse, BookingSlot, StructuredAgentMessage
from common.cache import TTLMemoryCache
from common.rate_limiter import SlidingWindowRateLimiter
from common.auth import verify_a2a_bearer_token, A2A_SECRET_TOKEN
from common.telemetry import trace_step, get_trace, clear_trace
from common.dialogue_store import SharedDialogueStore
from common.a2a_client import call_remote_a2a_agents_parallel


class TestOptimizations(unittest.TestCase):

    def setUp(self):
        # Clear test session from dialogues file
        from common.dialogue_store import DIALOGUES_FILE, _read_json, _write_json
        if DIALOGUES_FILE.exists():
            dialogues = _read_json(DIALOGUES_FILE, [])
            dialogues = [m for m in dialogues if m.get("session_id") != "test_session_opt_123"]
            _write_json(DIALOGUES_FILE, dialogues)

    def test_pydantic_schemas(self):
        slot = BookingSlot(time="14:00", master_name="Anna", available=True)
        resp = BookingResponse(
            status="slots_available",
            service_name="Hair Coloring",
            date="2026-08-07",
            available_slots=[slot],
        )
        self.assertEqual(resp.service_name, "Hair Coloring")
        self.assertEqual(len(resp.available_slots), 1)

        btn = ActionButton(label="Book 14:00", payload="BOOK_1400")
        msg = StructuredAgentMessage(
            text_response="Slots available on Friday!",
            agent_id="booking_agent",
            buttons=[btn],
        )
        self.assertEqual(msg.buttons[0].label, "Book 14:00")

    def test_ttl_cache(self):
        cache = TTLMemoryCache()
        cache.set("test_key", {"data": "hello"}, ttl_seconds=2)
        val = cache.get("test_key")
        self.assertIsNotNone(val)
        self.assertEqual(val["data"], "hello")

    def test_rate_limiter(self):
        limiter = SlidingWindowRateLimiter(requests_per_minute=2)
        self.assertTrue(limiter.is_allowed("client_1"))
        self.assertTrue(limiter.is_allowed("client_1"))
        self.assertFalse(limiter.is_allowed("client_1"))  # 3rd request blocked

    def test_a2a_auth(self):
        valid = verify_a2a_bearer_token(f"Bearer {A2A_SECRET_TOKEN}")
        self.assertTrue(valid)
        invalid = verify_a2a_bearer_token("Bearer wrong-token")
        self.assertFalse(invalid)

    def test_session_memory_context(self):
        test_session = "test_session_opt_123"
        SharedDialogueStore.add_message(test_session, "user", "Hi salon!", "web_widget", "EN")
        SharedDialogueStore.add_message(test_session, "agent", "Hello! How can I help?", "web_widget", "EN")

        context = SharedDialogueStore.get_session_context(test_session, limit=5)
        self.assertGreaterEqual(len(context), 2)
        self.assertEqual(context[0]["content"], "Hi salon!")

    def test_telemetry_tracing(self):
        trace_id = "test_trace_999"
        clear_trace(trace_id)
        with trace_step(trace_id, "TestStep"):
            pass
        spans = get_trace(trace_id)
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0]["step_name"], "TestStep")
        self.assertEqual(spans[0]["status"], "OK")
        self.assertIn("duration_ms", spans[0])

    def test_parallel_a2a_execution(self):
        async def run_parallel():
            # Mock calls
            calls = [
                ("hair_care_agent", "Query hair coloring advice"),
                ("navigation_agent", "Query travel route"),
            ]
            results = await call_remote_a2a_agents_parallel(calls, trace_id="parallel_test")
            return results

        results = asyncio.run(run_parallel())
        self.assertEqual(len(results), 2)


if __name__ == "__main__":
    unittest.main()
