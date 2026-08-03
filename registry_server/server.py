"""Standalone Agent Registry Server (MCP & A2A Yellow Pages Service).

Exposes an MCP interface and HTTP endpoints for registering, searching, and managing agent cards.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

from common.health_checker import attach_health_routes

app = FastAPI(
    title="Beauty Care Agent Registry",
    description="Decentralized Agent Service Mesh & Yellow Pages for Salon Micro-Agents",
    version="1.0.0",
)

attach_health_routes(app, service_name="beauty_care_agent_registry")

# In-memory storage for registered Agent Cards
_registered_agents: Dict[str, Dict[str, Any]] = {}


class AgentInterface(BaseModel):
    url: str
    protocol: str = "A2A"


class AgentSkill(BaseModel):
    id: str
    description: str
    tags: List[str] = Field(default_factory=list)


class AgentRegistration(BaseModel):
    agent_id: str
    name: str
    description: str
    version: str = "1.0.0"
    interfaces: List[AgentInterface]
    skills: List[AgentSkill]


@app.post("/api/v1/agents/register", status_code=status.HTTP_201_CREATED)
async def register_agent(agent: AgentRegistration) -> Dict[str, Any]:
    """Register or update an agent card in the registry catalog."""
    _registered_agents[agent.agent_id] = agent.model_dump()
    return {"status": "registered", "agent_id": agent.agent_id}


@app.get("/api/v1/agents/search")
async def search_agents(query: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search registered agents by keyword query or skill tag."""
    results = []
    for agent in _registered_agents.values():
        match = True
        if tag:
            tags = [t.lower() for skill in agent.get("skills", []) for t in skill.get("tags", [])]
            if tag.lower() not in tags:
                match = False
        if query and match:
            q = query.lower()
            name_desc = f"{agent['name']} {agent['description']}".lower()
            skill_match = any(q in s.get("id", "").lower() or q in s.get("description", "").lower() for s in agent.get("skills", []))
            if q not in name_desc and not skill_match:
                match = False
        if match:
            results.append(agent)
    return results


@app.get("/api/v1/agents/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get full registration details for a specific agent ID."""
    if agent_id not in _registered_agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found in registry")
    return _registered_agents[agent_id]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
