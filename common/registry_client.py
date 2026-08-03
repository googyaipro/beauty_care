"""Thin wrapper around Agent Registry client for Beauty Care platform."""

import os
from google.adk.integrations.agent_registry import AgentRegistry


def get_registry() -> AgentRegistry:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "beauty-care-platform")
    location = os.environ.get("AGENT_REGISTRY_LOCATION", "global")
    return AgentRegistry(project_id=project, location=location)


def parent_path() -> str:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "beauty-care-platform")
    location = os.environ.get("AGENT_REGISTRY_LOCATION", "global")
    return f"projects/{project}/locations/{location}"
