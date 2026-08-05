"""Thin wrapper around Agent Registry client for Beauty Care platform."""

import os
try:
    from google.adk.integrations.agent_registry import AgentRegistry
    HAS_ADK = True
except ImportError:
    HAS_ADK = False

    class AgentRegistry:
        def __init__(self, project_id: str, location: str):
            self.project_id = project_id
            self.location = location

        def get_agent_info(self, name: str) -> dict:
            return {"protocols": [{"interfaces": [{"url": "http://localhost:8000"}]}]}


def get_registry() -> AgentRegistry:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "beauty-care-platform")
    location = os.environ.get("AGENT_REGISTRY_LOCATION", "global")
    return AgentRegistry(project_id=project, location=location)



def parent_path() -> str:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "beauty-care-platform")
    location = os.environ.get("AGENT_REGISTRY_LOCATION", "global")
    return f"projects/{project}/locations/{location}"
