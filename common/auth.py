"""Shared GCP Service Account & Auth Helper for Beauty Care Platform.

Loads service-account-key.json via Google Application Default Credentials (ADC),
file path, OR direct JSON environment variable SERVICE_ACCOUNT_KEY_JSON.
"""

import json
import os
from pathlib import Path
from typing import Dict

import google.auth
import google.auth.transport.requests
from google.oauth2 import service_account

KEY_PATH = Path("/app/service-account-key.json")
LOCAL_KEY_PATH = Path(__file__).resolve().parent.parent / "service-account-key.json"


def get_service_account_credentials():
    """Load Google Service Account credentials from JSON env string, JSON file, or ADC."""
    scopes = [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/calendar",
    ]

    # Option 1: Direct JSON string in Environment Variable (e.g. pasted in Dokploy UI)
    json_env = os.environ.get("SERVICE_ACCOUNT_KEY_JSON")
    if json_env and json_env.strip().startswith("{"):
        try:
            info = json.loads(json_env)
            return service_account.Credentials.from_service_account_info(info, scopes=scopes)
        except Exception as exc:
            print(f"Error parsing SERVICE_ACCOUNT_KEY_JSON: {exc}")

    # Option 2: File path on disk
    key_file = None
    if KEY_PATH.exists():
        key_file = str(KEY_PATH)
    elif LOCAL_KEY_PATH.exists():
        key_file = str(LOCAL_KEY_PATH)
    elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        key_file = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

    if key_file and os.path.exists(key_file):
        try:
            return service_account.Credentials.from_service_account_file(key_file, scopes=scopes)
        except Exception as exc:
            print(f"Error loading key file {key_file}: {exc}")

    # Option 3: Standard GCP ADC Fallback
    credentials, _ = google.auth.default()
    return credentials


def get_dynamic_headers(context=None) -> Dict[str, str]:
    """Fetch fresh OIDC headers each call to avoid token expiry."""
    try:
        credentials = get_service_account_credentials()
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        quota_project_id = getattr(credentials, "quota_project_id", None) or os.environ.get("GOOGLE_CLOUD_PROJECT", "beauty-care-platform")
        if quota_project_id:
            headers["x-goog-user-project"] = quota_project_id
        return headers
    except Exception:
        return {"Content-Type": "application/json"}
