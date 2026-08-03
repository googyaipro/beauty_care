"""DIKIDI / YClients CRM MCP Server.

Provides Model Context Protocol (MCP) tools for checking available slots,
fetching service prices, creating bookings, and rescheduling/canceling appointments.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

from common.health_checker import attach_health_routes

app = FastAPI(
    title="DIKIDI CRM MCP Server",
    description="MCP Tool Interface for DIKIDI Business / YClients CRM Integration",
    version="1.0.0",
)

attach_health_routes(app, service_name="dikidi_crm_mcp")

# Mock CRM Database for development & testing
_mock_services = [
    {"id": "serv_101", "category": "hair", "name": "Стрижка и укладка (Haircut & Styling)", "duration_min": 60, "price": 50.0, "currency": "USD"},
    {"id": "serv_102", "category": "hair", "name": "Сложное окрашивание (Hair Coloring)", "duration_min": 150, "price": 120.0, "currency": "USD"},
    {"id": "serv_201", "category": "cosmetology", "name": "Чистка лица (Facial Cleansing)", "duration_min": 90, "price": 75.0, "currency": "USD"},
    {"id": "serv_202", "category": "cosmetology", "name": "Пилинг уход (Peeling Care)", "duration_min": 45, "price": 60.0, "currency": "USD"},
    {"id": "serv_301", "category": "nails", "name": "Маникюр с покрытием (Manicure)", "duration_min": 60, "price": 40.0, "currency": "USD"},
]

_mock_bookings: Dict[str, Dict[str, Any]] = {}


class BookingRequest(BaseModel):
    client_id: str
    service_id: str
    master_name: str
    date: str
    time: str
    language: str = "en"
    deposit_paid: bool = False


@app.get("/mcp/tools/get_services")
async def get_services(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """MCP Tool: Fetch available salon services and prices."""
    if category:
        return [s for s in _mock_services if s["category"].lower() == category.lower()]
    return _mock_services


@app.get("/mcp/tools/get_available_slots")
async def get_available_slots(service_id: str, date: str, master_name: Optional[str] = None) -> Dict[str, Any]:
    """MCP Tool: Check open time slots for a given service and date."""
    # Returns available slots for booking
    return {
        "service_id": service_id,
        "date": date,
        "master_name": master_name or "Anna (Top Stylist)",
        "available_slots": ["10:00", "12:30", "15:00", "17:30"],
    }


@app.post("/mcp/tools/create_booking", status_code=status.HTTP_201_CREATED)
async def create_booking(booking: BookingRequest) -> Dict[str, Any]:
    """MCP Tool: Create official appointment entry in DIKIDI CRM."""
    booking_id = f"bk_{int(datetime.now(timezone.utc).timestamp())}"
    record = {
        "booking_id": booking_id,
        "status": "confirmed" if booking.deposit_paid else "pending_deposit",
        **booking.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _mock_bookings[booking_id] = record
    return {
        "status": "success",
        "booking_id": booking_id,
        "message": f"Appointment booked for {booking.date} at {booking.time}",
        "details": record,
    }


@app.post("/mcp/tools/cancel_booking")
async def cancel_booking(booking_id: str) -> Dict[str, Any]:
    """MCP Tool: Cancel appointment in DIKIDI CRM."""
    if booking_id not in _mock_bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    _mock_bookings[booking_id]["status"] = "cancelled"
    return {"status": "cancelled", "booking_id": booking_id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8015)
