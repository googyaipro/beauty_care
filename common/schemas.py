"""Pydantic / Dataclass Structured Output Schemas for Beauty Care Multi-Agent Platform."""

from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    from dataclasses import dataclass, field

    class BaseModel:
        def model_dump(self) -> Dict[str, Any]:
            res = {}
            for k, v in self.__dict__.items():
                if hasattr(v, "model_dump"):
                    res[k] = v.model_dump()
                elif isinstance(v, list):
                    res[k] = [item.model_dump() if hasattr(item, "model_dump") else item for item in v]
                else:
                    res[k] = v
            return res

    def Field(default=None, default_factory=None, description=""):
        if default_factory is not None:
            return field(default_factory=default_factory)
        return field(default=default)


if HAS_PYDANTIC:
    class BookingSlot(BaseModel):
        time: str = Field(description="Time slot in HH:MM format e.g. 14:00")
        master_name: str = Field(default="Anna", description="Name of the beauty master")
        master_id: str = Field(default="master_1", description="Identifier of the master")
        available: bool = Field(default=True, description="Whether slot is open for booking")

    class BookingResponse(BaseModel):
        status: str = Field(default="slots_available", description="Status e.g. slots_available, booking_created, cancelled")
        service_name: str = Field(description="Name of requested service e.g. Hair Coloring")
        date: str = Field(description="Target date YYYY-MM-DD")
        available_slots: List[BookingSlot] = Field(default_factory=list)
        confirmation_code: Optional[str] = Field(default=None, description="Booking reference code")

    class NavigationRouteResponse(BaseModel):
        destination_name: str = Field(default="Beauty Care Salon", description="Target destination")
        transport_mode: str = Field(default="transit", description="transit, driving, or walking")
        duration_minutes: int = Field(description="Estimated travel duration in minutes")
        distance_km: float = Field(description="Distance in kilometers")
        google_maps_url: str = Field(description="Direct navigation link e.g. https://maps.google.com/...")

    class ActionButton(BaseModel):
        label: str = Field(description="Button display text e.g. Book 14:00")
        payload: str = Field(description="Action payload e.g. BOOK_1400")
        url: Optional[str] = Field(default=None, description="Optional external link")

    class StructuredAgentMessage(BaseModel):
        text_response: str = Field(description="Natural language text response for client")
        agent_id: str = Field(description="ID of the responding agent")
        confidence: float = Field(default=1.0, description="Confidence score 0.0 to 1.0")
        buttons: List[ActionButton] = Field(default_factory=list, description="Interactive buttons for Telegram/WhatsApp")
        metadata: Dict[str, Any] = Field(default_factory=dict, description="Structured payload e.g. booking or route details")

else:
    @dataclass
    class BookingSlot(BaseModel):
        time: str
        master_name: str = "Anna"
        master_id: str = "master_1"
        available: bool = True

    @dataclass
    class BookingResponse(BaseModel):
        service_name: str
        date: str
        status: str = "slots_available"
        available_slots: List[BookingSlot] = Field(default_factory=list)
        confirmation_code: Optional[str] = None

    @dataclass
    class NavigationRouteResponse(BaseModel):
        duration_minutes: int
        distance_km: float
        google_maps_url: str
        destination_name: str = "Beauty Care Salon"
        transport_mode: str = "transit"

    @dataclass
    class ActionButton(BaseModel):
        label: str
        payload: str
        url: Optional[str] = None

    @dataclass
    class StructuredAgentMessage(BaseModel):
        text_response: str
        agent_id: str
        confidence: float = 1.0
        buttons: List[ActionButton] = Field(default_factory=list)
        metadata: Dict[str, Any] = Field(default_factory=dict)
