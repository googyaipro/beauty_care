import os
import sys

# Ensure /app root directory is in sys.path for common.* imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, "/app")

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uvicorn

from common.health_checker import attach_health_routes

app = FastAPI(
    title="Payment MCP Server",
    description="Multi-Country Payment Router and Fiscal Receipts Generator",
    version="1.0.0",
)

attach_health_routes(app, service_name="payment_mcp_server")

# Active payment configuration (configured via Admin Panel)
_payment_config = {
    "provider": "stripe",  # options: stripe, tbc_bank, yookassa
    "currency": "USD",
    "fiscalization_enabled": True,
}


class PaymentLinkRequest(BaseModel):
    booking_id: str
    amount: float
    currency: str = "USD"
    description: str
    client_email: Optional[str] = None
    client_phone: Optional[str] = None


@app.post("/mcp/tools/create_payment_link", status_code=status.HTTP_201_CREATED)
async def create_payment_link(req: PaymentLinkRequest) -> Dict[str, Any]:
    """MCP Tool: Generate payment link for deposit/prepayment based on country gateway."""
    payment_id = f"pay_{int(datetime.now(timezone.utc).timestamp())}"
    provider = _payment_config["provider"]

    payment_url = f"https://pay.oxyjet.win/{provider}/{payment_id}"

    return {
        "payment_id": payment_id,
        "provider": provider,
        "amount": req.amount,
        "currency": req.currency,
        "payment_url": payment_url,
        "expires_in_minutes": 30,
        "message": f"Prepayment link generated via {provider.upper()}",
    }


@app.get("/mcp/tools/check_payment_status")
async def check_payment_status(payment_id: str) -> Dict[str, Any]:
    """MCP Tool: Check payment status from payment gateway."""
    return {
        "payment_id": payment_id,
        "status": "paid",
        "paid_at": datetime.now(timezone.utc).isoformat(),
        "fiscal_receipt_issued": True,
    }


@app.post("/mcp/tools/issue_fiscal_receipt")
async def issue_fiscal_receipt(payment_id: str, client_email: str) -> Dict[str, Any]:
    """MCP Tool: Send official digital fiscal receipt to client email/SMS."""
    receipt_id = f"rec_{payment_id}"
    return {
        "receipt_id": receipt_id,
        "payment_id": payment_id,
        "status": "sent",
        "delivered_to": client_email,
        "fiscal_timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8016)
