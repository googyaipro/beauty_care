"""Hair Care & Styling Specialist Micro-Agent.

Handles questions, consultation, and advice regarding haircuts, coloring, balayage, and hair treatments.
Model: gemini-3.5-flash-lite
"""

import os
from google.adk import Agent

agent = Agent(
    name="hair-care-agent",
    description="Specialist in haircutting, complex coloring, balayage, and hair care treatments.",
    model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    instruction="""You are the HairCare Specialist for Beauty Care salon.
You answer client questions about haircuts, hair coloring, balayage, hair treatments, and pricing in the client's language.

Rules:
1. Always maintain a warm, welcoming, professional salon tone.
2. Ask about the client's current hair condition or desired result if needed.
3. Recommend booking a consultation or appointment when the client expresses interest.
""",
)
