import asyncio
import uuid

try:
    import httpx
    from a2a.client import ClientConfig, ClientFactory
    from a2a.types import AgentCard, Message, Part, Role, TextPart
    HAS_A2A = True
except ImportError:
    HAS_A2A = False

from common.registry_client import get_registry


async def call_remote_a2a_agent(agent_resource_name: str, message: str, trace_id: str = "default") -> dict:
    """Send a message to an A2A agent registered in the Agent Registry."""
    if not HAS_A2A:
        return {"response": f"[Simulated Response from {agent_resource_name}]: Processed message: '{message}'", "agent_url": "http://localhost:8000"}
    try:
        registry = get_registry()

        info = registry.get_agent_info(agent_resource_name)
        interfaces = info.get("protocols", [{}])[0].get("interfaces", [])
        if not interfaces:
            return {"error": f"Agent has no A2A interface: {agent_resource_name}"}
        url = interfaces[0]["url"].rstrip("/")
        card_url = f"{url}/.well-known/agent-card.json"

        async with httpx.AsyncClient(timeout=180.0) as http:
            resp = await http.get(card_url)
            if resp.status_code != 200:
                return {"error": f"Could not fetch agent card at {card_url} ({resp.status_code})"}
            card = AgentCard.model_validate(resp.json())

            factory = ClientFactory(config=ClientConfig(httpx_client=http, streaming=False))
            client = factory.create(card)
            msg = Message(
                kind="message",
                message_id=str(uuid.uuid4()),
                role=Role.user,
                parts=[Part(root=TextPart(kind="text", text=message))],
            )

            response_text_parts: list[str] = []
            async for event in client.send_message(msg):
                if isinstance(event, tuple):
                    for e in event:
                        if e is None or not hasattr(e, "history") or not e.history:
                            continue
                        for m in e.history:
                            if getattr(m, "role", None) != Role.agent or not m.parts:
                                continue
                            for p in m.parts:
                                if hasattr(p.root, "text") and p.root.text:
                                    response_text_parts.append(p.root.text)

            if not response_text_parts:
                return {"error": "Agent returned no text response", "url": url}
            return {"response": "\n".join(response_text_parts), "agent_url": url}
    except Exception as exc:
        return {"error": f"Error calling A2A agent: {str(exc)}"}


async def call_remote_a2a_agents_parallel(agent_calls: list[tuple[str, str]], trace_id: str = "default") -> list[dict]:
    """Execute multiple A2A agent calls in parallel via asyncio.gather."""
    tasks = [
        call_remote_a2a_agent(agent_name, msg, trace_id=trace_id)
        for agent_name, msg in agent_calls
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)
