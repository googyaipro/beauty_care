"""End-to-End Integration tests for Beauty Care Multi-Agent Platform."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from registry_server.server import app as registry_app
from mcp_servers.google_calendar_crm_mcp.server import app as gcal_crm_app
from mcp_servers.payment_mcp.server import app as payment_app
from mcp_servers.maps_mcp.server import app as maps_app
from gateways.telegram_gateway import app as telegram_app
from gateways.whatsapp_gateway import app as whatsapp_app
from admin_cms.app import app as admin_app


def test_registry_server() -> None:
    client = TestClient(registry_app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_google_calendar_crm_mcp() -> None:
    client = TestClient(gcal_crm_app)

    services_resp = client.get("/mcp/tools/get_services?category=hair")
    assert services_resp.status_code == 200
    assert len(services_resp.json()) >= 1

    booking_resp = client.post(
        "/mcp/tools/create_booking",
        json={
            "client_id": "c_101",
            "service_id": "serv_101",
            "master_name": "Anna",
            "date": "2026-08-10",
            "time": "14:00",
            "language": "en",
        },
    )
    assert booking_resp.status_code == 201
    assert booking_resp.json()["status"] == "success"
    assert booking_resp.json()["calendar_provider"] == "google_calendar"


def test_payment_mcp_server() -> None:
    client = TestClient(payment_app)

    pay_resp = client.post(
        "/mcp/tools/create_payment_link",
        json={
            "booking_id": "bk_123",
            "amount": 25.0,
            "currency": "USD",
            "description": "Haircut deposit",
        },
    )
    assert pay_resp.status_code == 201
    assert "payment_url" in pay_resp.json()


def test_google_maps_mcp() -> None:
    client = TestClient(maps_app)

    route_resp = client.post(
        "/mcp/tools/calculate_route",
        json={
            "client_origin": "Central Station",
            "language": "ru",
        },
    )
    assert route_resp.status_code == 200
    assert "google_maps_link" in route_resp.json()


def test_telegram_gateway() -> None:
    client = TestClient(telegram_app)

    tg_resp = client.post(
        "/v1/webhook/telegram",
        json={
            "update_id": 1,
            "message": {
                "chat": {"id": 998877},
                "text": "Здравствуйте, хочу записаться на завтра!",
            },
        },
    )
    assert tg_resp.status_code == 200


def test_admin_cms_audio_toggle() -> None:
    client = TestClient(admin_app)

    toggle_resp = client.post(
        "/api/v1/admin/settings/audio_toggle",
        json={"enabled": True},
    )
    assert toggle_resp.status_code == 200


if __name__ == "__main__":
    test_registry_server()
    test_google_calendar_crm_mcp()
    test_payment_mcp_server()
    test_google_maps_mcp()
    test_telegram_gateway()
    test_admin_cms_audio_toggle()
    print("All End-to-End Integration tests passed successfully!")
