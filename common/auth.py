"""Shared GCP Service Account & Auth Helper for Beauty Care Platform.

Loads service-account-key.json via Google Application Default Credentials (ADC)
and manages OIDC OAuth2 Bearer Tokens for Vertex AI, Google Calendar API, and Google Maps API.
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
    """Load Google Service Account credentials from JSON key file or environment."""
    key_file = None
    if KEY_PATH.exists():
        key_file = str(KEY_PATH)
    elif LOCAL_KEY_PATH.exists():
        key_file = str(LOCAL_KEY_PATH)
    elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        key_file = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

    if key_file and os.path.exists(key_file):
        scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/calendar",
        ]
        return service_account.Credentials.from_service_account_file(key_file, scopes=scopes)
    
    # Fallback to standard ADC
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
