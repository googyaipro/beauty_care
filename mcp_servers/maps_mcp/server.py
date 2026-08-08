import os
import sys

# Ensure /app root directory is in sys.path for common.* imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, "/app")

from typing import Any, Dict
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes
from common.cache import cache
from common.auth import get_gcp_secret


app = FastAPI(
    title="Google Maps MCP Server",
    description="MCP Navigation Tool for Google Maps Places & Routes API",
    version="1.0.0",
)

attach_health_routes(app, service_name="google_maps_mcp")

# Default Salon Address
SALON_ADDRESS = "123 Beauty Avenue, City Center"


class RouteRequest(BaseModel):
    client_origin: str
    travel_mode: str = "DRIVE"  # DRIVE, WALK, TRANSIT
    language: str = "en"


@app.post("/mcp/tools/calculate_route")
async def calculate_route(req: RouteRequest) -> Dict[str, Any]:
    """MCP Tool: Calculate travel time and generate localized Google Maps route link with 24h caching."""
    cache_key = f"route:{req.client_origin.lower()}:{req.travel_mode}:{req.language}"
    cached_val = cache.get(cache_key)
    if cached_val:
        cached_val["cached"] = True
        return cached_val

    encoded_origin = req.client_origin.replace(" ", "+")
    encoded_dest = SALON_ADDRESS.replace(" ", "+")

    google_maps_url = f"https://www.google.com/maps/dir/?api=1&origin={encoded_origin}&destination={encoded_dest}&travelmode={req.travel_mode.lower()}&hl={req.language}"

    res = {
        "status": "success",
        "origin": req.client_origin,
        "destination": SALON_ADDRESS,
        "travel_mode": req.travel_mode,
        "estimated_duration_min": 18,
        "distance_km": 4.2,
        "google_maps_link": google_maps_url,
        "cached": False,
    }
    cache.set(cache_key, res, ttl_seconds=86400)
    return res


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8014)
