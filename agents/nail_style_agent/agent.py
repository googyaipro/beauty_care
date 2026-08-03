"""Nail Style Specialist Micro-Agent.

Handles questions regarding manicure, pedicure, gel polish, and nail art designs.
Model: gemini-3.5-flash-lite
"""

import os
from google.adk import Agent

agent = Agent(
    name="nail-style-agent",
    description="Specialist in manicure, pedicure, nail extensions, and nail art design.",
    model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    instruction="""You are the Nail Style Specialist for Beauty Care salon.
You assist clients with selecting manicure, pedicure, gel coating, and nail design options.

Rules:
1. Explain duration and care tips for gel polish and nail strengthening.
2. Encourage booking an appointment with top nail masters.
""",
)
