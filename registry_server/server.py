import os
import sys

# Ensure /app root directory is in sys.path for common.* imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/app")

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


# Default built-in Agents in the Beauty Care Mesh
_default_agents = {
    "concierge-agent": {
        "agent_id": "concierge-agent",
        "name": "Concierge Receptionist Agent",
        "description": "Первичный ИИ-администратор салона, приветствие и диспетчеризация запросов клиентов",
        "version": "1.0.0",
        "interfaces": [{"url": "https://beauty-api.oxyjet.win/v1/webhook/telegram", "protocol": "A2A"}],
        "skills": [{"id": "greeting", "description": "Приветствие и маршрутизация", "tags": ["reception", "routing", "general"]}],
    },
    "haircare-specialist": {
        "agent_id": "haircare-specialist",
        "name": "Haircare & Coloring Specialist Agent",
        "description": "Эксперт по уходу за волосами, стрижкам и сложному окрашиванию",
        "version": "1.0.0",
        "interfaces": [{"url": "https://beauty-api.oxyjet.win/v1/webhook/telegram", "protocol": "A2A"}],
        "skills": [{"id": "hair_coloring", "description": "Стрижка и окрашивание волос", "tags": ["hair", "coloring", "haircut"]}],
    },
    "cosmetology-specialist": {
        "agent_id": "cosmetology-specialist",
        "name": "Cosmetology & Facial Care Specialist Agent",
        "description": "Эксперт по уходу за кожей лица, чистке и пилингу",
        "version": "1.0.0",
        "interfaces": [{"url": "https://beauty-api.oxyjet.win/v1/webhook/telegram", "protocol": "A2A"}],
        "skills": [{"id": "facial_care", "description": "Чистка лица и пилинг", "tags": ["cosmetology", "facial", "skin"]}],
    },
    "nailstyle-specialist": {
        "agent_id": "nailstyle-specialist",
        "name": "Nail Style Specialist Agent",
        "description": "Мастер ногтевого сервиса, маникюр и педикюр",
        "version": "1.0.0",
        "interfaces": [{"url": "https://beauty-api.oxyjet.win/v1/webhook/telegram", "protocol": "A2A"}],
        "skills": [{"id": "manicure", "description": "Маникюр с покрытием", "tags": ["nails", "manicure"]}],
    },
    "navigation-specialist": {
        "agent_id": "navigation-specialist",
        "name": "Google Maps Navigation Agent",
        "description": "Расчет оптимального маршрута и времени в пути до салона через Google Maps API",
        "version": "1.0.0",
        "interfaces": [{"url": "https://beauty-api.oxyjet.win/mcp/tools/calculate_route", "protocol": "MCP"}],
        "skills": [{"id": "route_calculation", "description": "Расчет маршрута Google Maps", "tags": ["maps", "navigation", "route"]}],
    },
    "booking-crm-specialist": {
        "agent_id": "booking-crm-specialist",
        "name": "Google Calendar CRM Agent",
        "description": "Поиск свободных окон и автоматическая запись клиентов в Google Календарь",
        "version": "1.0.0",
        "interfaces": [{"url": "https://beauty-api.oxyjet.win/mcp/tools/create_booking", "protocol": "MCP"}],
        "skills": [{"id": "calendar_booking", "description": "Запись в Google Календарь", "tags": ["calendar", "crm", "booking"]}],
    },
}

_registered_agents: Dict[str, Dict[str, Any]] = dict(_default_agents)


@app.get("/api/v1/agents", summary="List all registered agent IDs and cards")
async def list_agents() -> List[Dict[str, Any]]:
    """Get complete list of all registered agents in the Beauty Care platform."""
    return list(_registered_agents.values())


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
