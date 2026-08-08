"""Shared GCP Service Account & Auth Helper for Beauty Care Platform.

Loads service-account-key.json via Google Application Default Credentials (ADC),
file path, OR direct JSON environment variable SERVICE_ACCOUNT_KEY_JSON.
Never crashes on startup if key file is missing.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

try:
    import google.auth
    import google.auth.transport.requests
    from google.oauth2 import service_account
    HAS_GOOGLE_AUTH = True
except ImportError:
    HAS_GOOGLE_AUTH = False


KEY_PATH = Path("/app/service-account-key.json")
LOCAL_KEY_PATH = Path(__file__).resolve().parent.parent / "service-account-key.json"
TMP_KEY_PATH = Path("/tmp/service-account-key.json")

# Auto-dump SERVICE_ACCOUNT_KEY_JSON to /tmp/service-account-key.json so Google ADK / GenAI SDK ADC works out-of-the-box
json_env = os.environ.get("SERVICE_ACCOUNT_KEY_JSON")
if json_env and json_env.strip().startswith("{"):
    try:
        TMP_KEY_PATH.write_text(json_env.strip(), encoding="utf-8")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(TMP_KEY_PATH)
    except Exception as exc:
        print(f"Error writing /tmp/service-account-key.json: {exc}")


def get_service_account_credentials():
    """Load Google Service Account credentials from JSON env string, JSON file, or ADC."""
    if not HAS_GOOGLE_AUTH:
        return None

    scopes = [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/calendar",
    ]

    # Option 1: Direct JSON string in Environment Variable
    json_str = os.environ.get("SERVICE_ACCOUNT_KEY_JSON")
    if json_str and json_str.strip().startswith("{"):
        try:
            info = json.loads(json_str)
            return service_account.Credentials.from_service_account_info(info, scopes=scopes)
        except Exception as exc:
            print(f"Error parsing SERVICE_ACCOUNT_KEY_JSON: {exc}")

    # Option 2: File path on disk
    key_file = None
    if TMP_KEY_PATH.exists():
        key_file = str(TMP_KEY_PATH)
    elif KEY_PATH.exists():
        key_file = str(KEY_PATH)
    elif LOCAL_KEY_PATH.exists():
        key_file = str(LOCAL_KEY_PATH)
    elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        env_file = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        if os.path.exists(env_file):
            key_file = env_file

    if key_file and os.path.exists(key_file):
        try:
            return service_account.Credentials.from_service_account_file(key_file, scopes=scopes)
        except Exception as exc:
            print(f"Error loading key file {key_file}: {exc}")

    # Option 3: Standard GCP ADC Fallback (fail-safe)
    try:
        credentials, _ = google.auth.default(scopes=scopes)
        return credentials
    except Exception as exc:
        print(f"GCP ADC fallback unavailable: {exc}")
        return None


def get_dynamic_headers(context=None) -> Dict[str, str]:
    """Fetch fresh OIDC headers each call to avoid token expiry."""
    try:
        credentials = get_service_account_credentials()
        if credentials:
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
        pass

    return {"Content-Type": "application/json"}


def get_gcp_secret(secret_id: str, default: str = "") -> str:
    """Fetch secret value from environment variable OR GCP Secret Manager."""
    val = os.environ.get(secret_id)
    if val and val.strip():
        return val.strip()

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "beauty-care-platform")
    try:
        from google.cloud import secretmanager
        creds = get_service_account_credentials()
        client = secretmanager.SecretManagerServiceClient(credentials=creds)
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception:
        pass

    return default


A2A_SECRET_TOKEN = os.environ.get("A2A_SECRET_TOKEN", "beauty-care-a2a-secret-2026")


def verify_a2a_bearer_token(auth_header: str) -> bool:
    """Verify that incoming A2A HTTP request contains valid Bearer token."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ", 1)[1].strip()
    return token == A2A_SECRET_TOKEN

