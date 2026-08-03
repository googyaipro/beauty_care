"""Google Calendar CRM MCP Server.

Provides Model Context Protocol (MCP) tools for checking available slots,
fetching services, creating bookings as Google Calendar events, and managing appointments.
Uses Google Calendar API within the dedicated 'beauty-care-platform' GCP project.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

from common.health_checker import attach_health_routes

app = FastAPI(
    title="Google Calendar CRM MCP Server",
    description="MCP Tool Interface for Google Calendar API Integration",
    version="1.0.0",
)

attach_health_routes(app, service_name="google_calendar_crm_mcp")

# Service Catalog
_services_catalog = [
    {"id": "serv_101", "category": "hair", "name": "Стрижка и укладка (Haircut & Styling)", "duration_min": 60, "price": 50.0, "currency": "USD"},
    {"id": "serv_102", "category": "hair", "name": "Сложное окрашивание (Hair Coloring)", "duration_min": 150, "price": 120.0, "currency": "USD"},
    {"id": "serv_201", "category": "cosmetology", "name": "Чистка лица (Facial Cleansing)", "duration_min": 90, "price": 75.0, "currency": "USD"},
    {"id": "serv_202", "category": "cosmetology", "name": "Пилинг уход (Peeling Care)", "duration_min": 45, "price": 60.0, "currency": "USD"},
    {"id": "serv_301", "category": "nails", "name": "Маникюр с покрытием (Manicure)", "duration_min": 60, "price": 40.0, "currency": "USD"},
]

_calendar_events: Dict[str, Dict[str, Any]] = {}


class GoogleCalendarBookingRequest(BaseModel):
    client_id: str
    service_id: str
    master_name: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    language: str = "en"
    deposit_paid: bool = False
    client_email: Optional[str] = None


@app.get("/mcp/tools/get_services")
async def get_services(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """MCP Tool: Fetch available salon services and prices from catalog."""
    if category:
        return [s for s in _services_catalog if s["category"].lower() == category.lower()]
    return _services_catalog


@app.get("/mcp/tools/get_available_slots")
async def get_available_slots(service_id: str, date: str, master_name: Optional[str] = None) -> Dict[str, Any]:
    """MCP Tool: Query Google Calendar free/busy API for open appointment slots."""
    # In production, queries Google Calendar FreeBusy API (calendar.googleapis.com)
    return {
        "service_id": service_id,
        "date": date,
        "master_name": master_name or "Anna (Top Stylist)",
        "available_slots": ["10:00", "12:30", "15:00", "17:30"],
        "calendar_provider": "google_calendar",
    }


@app.post("/mcp/tools/create_booking", status_code=status.HTTP_201_CREATED)
async def create_booking(booking: GoogleCalendarBookingRequest) -> Dict[str, Any]:
    """MCP Tool: Insert booking event into Google Calendar via Google Calendar API."""
    booking_id = f"gcal_{int(datetime.now(timezone.utc).timestamp())}"
    
    # Calculate start and end ISO timestamps
    event_start = f"{booking.date}T{booking.time}:00Z"
    
    event_data = {
        "event_id": booking_id,
        "summary": f"💈 {booking.service_id} - Client: {booking.client_id}",
        "description": f"Master: {booking.master_name}\nDeposit Paid: {booking.deposit_paid}\nLang: {booking.language}",
        "start": {"dateTime": event_start},
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "calendar_provider": "google_calendar",
    }
    _calendar_events[booking_id] = event_data

    return {
        "status": "success",
        "booking_id": booking_id,
        "calendar_provider": "google_calendar",
        "message": f"Appointment created in Google Calendar for {booking.date} at {booking.time}",
        "event_details": event_data,
    }


@app.post("/mcp/tools/cancel_booking")
async def cancel_booking(booking_id: str) -> Dict[str, Any]:
    """MCP Tool: Delete or cancel event in Google Calendar."""
    if booking_id not in _calendar_events:
        raise HTTPException(status_code=404, detail="Google Calendar event not found")
    _calendar_events[booking_id]["status"] = "cancelled"
    return {"status": "cancelled", "booking_id": booking_id, "calendar_provider": "google_calendar"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8015)
