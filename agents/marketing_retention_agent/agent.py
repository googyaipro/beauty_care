"""LTV Retention & Waitlist Auto-Filler Micro-Agent.

Manages automated 28-45 day client reactivation touches and auto-filling hot slots from the waitlist.
Model: gemini-3.5-flash-lite
"""

import os
from google.adk import Agent

agent = Agent(
    name="marketing-retention-agent",
    description="Manages automated client reactivation touches and auto-filling cancelled appointment slots from waitlists.",
    model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    instruction="""You are the Client Retention Specialist for Beauty Care salon.

Tasks:
1. Re-engage clients whose last hair coloring or manicure was 28-45 days ago with a gentle, personalized invitation.
2. When an appointment slot opens up, notify clients on the waitlist with a special offer or discount.
""",
)
