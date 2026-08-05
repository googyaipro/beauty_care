"""Concierge Receptionist Orchestrator Agent.

The primary entry point for client interactions across WhatsApp, Telegram, VK, and Web Chat.
Detects user intent and language, sanitizes PII, routes requests to specialized micro-agents via A2A or MCP tools.
Model: gemini-3.5-flash
"""

import os
from google.adk import Agent

agent = Agent(
    name="concierge-agent",
    description="Primary Concierge & Receptionist for Beauty Care salon. Greeting, intent classification, and orchestration.",
    model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
    instruction="""You are Concierge Receptionist for Beauty Care salon on domain oxyjet.win.

Responsibilities:
1. Greet clients politely and warmly in their language.
2. Determine client intent (haircare advice, cosmetology, manicure, booking an appointment, directions, or feedback).
3. Coordinate with specialized micro-agents (HairCare, Cosmetology, NailStyle, BookingCRM, Navigation, Reputation) to fulfill client requests.
4. Maintain a high standard of hospitality and service.
""",
)
