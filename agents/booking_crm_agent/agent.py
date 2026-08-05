"""DIKIDI / YClients Booking Manager Micro-Agent.

Executes slot availability lookups, booking creation, prepayment link requests, and appointment cancellations.
Model: gemini-3.5-flash
"""

import os
from google.adk import Agent

agent = Agent(
    name="booking-crm-agent",
    description="Manages slot checks, appointment bookings, deposit payment links, and cancellations in DIKIDI CRM.",
    model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
    instruction="""You are the Booking Manager for Beauty Care salon.

Tasks:
1. Check open slots in DIKIDI Business CRM for requested date and service.
2. Confirm client appointments and request deposit payment link if deposit is required.
3. Handle rescheduling and cancellations gracefully.
""",
)
