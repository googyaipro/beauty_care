"""Google Maps Navigation Specialist Micro-Agent.

Calculates travel routes, travel time estimations, and builds Google Maps links.
Model: gemini-3.5-flash
"""

import os
from google.adk import Agent

agent = Agent(
    name="navigation-agent",
    description="Calculates travel routes and provides Google Maps directions to the salon.",
    model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
    instruction="""You are the Navigation Specialist for Beauty Care salon.
When a client asks for directions or provides their location, calculate estimated travel time and generate a direct Google Maps route link in their language.
""",
)
