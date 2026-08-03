"""Health Checker & Uptime Endpoint Module for Beauty Care Services.

Provides /healthz and /livez endpoints for container monitoring & Dokploy integration.
"""

from typing import Any, Dict
from fastapi import FastAPI, Response, status


def attach_health_routes(app: FastAPI, service_name: str, version: str = "0.1.0") -> None:
    """Attach /healthz and /livez health check routes to FastAPI application."""

    @app.get("/healthz", tags=["Health"])
    async def healthz() -> Dict[str, Any]:
        """Liveness & Readiness probe for Docker / Dokploy / Traefik monitoring."""
        return {
            "status": "ok",
            "service": service_name,
            "version": version,
        }

    @app.get("/livez", tags=["Health"])
    async def livez() -> Dict[str, Any]:
        """Simple liveness probe."""
        return {"status": "alive"}
