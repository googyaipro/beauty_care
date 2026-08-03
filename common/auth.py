"""Shared auth helper for Beauty Care Platform calls."""

import os
import google.auth
import google.auth.transport.requests


def get_dynamic_headers(context=None) -> dict:
    """Fetch fresh OIDC headers each call to avoid token expiry."""
    try:
        credentials, _ = google.auth.default()
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        quota_project_id = getattr(credentials, "quota_project_id", None) or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if quota_project_id:
            headers["x-goog-user-project"] = quota_project_id
        return headers
    except Exception:
        return {"Content-Type": "application/json"}
