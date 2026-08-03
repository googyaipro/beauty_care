"""Role-Based Access Control (RBAC) Module for Beauty Care Admin Panel.

Roles:
- SUPER_ADMIN: Full system control, API keys, logs, billing, prompts
- SALON_MANAGER: RAG Wiki editing, prices, masters, appointment calendar
- RECEPTIONIST: Appointment calendar read/write, client chat viewing
- MASTER: Read-only access to personal schedule
"""

from enum import Enum
from typing import Dict, List, Set


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    SALON_MANAGER = "salon_manager"
    RECEPTIONIST = "receptionist"
    MASTER = "master"


class Permission(str, Enum):
    # System & Security Permissions
    MANAGE_USERS = "manage_users"
    MANAGE_API_KEYS = "manage_api_keys"
    MANAGE_SYSTEM_PROMPTS = "manage_system_prompts"
    VIEW_AUDIT_LOGS = "view_audit_logs"

    # Business & Content Permissions
    MANAGE_RAG_WIKI = "manage_rag_wiki"
    MANAGE_PRICING = "manage_pricing"
    MANAGE_MASTERS = "manage_masters"
    CONFIGURE_PAYMENTS = "configure_payments"

    # Operational Permissions
    VIEW_ALL_APPOINTMENTS = "view_all_appointments"
    MANAGE_APPOINTMENTS = "manage_appointments"
    VIEW_PERSONAL_SCHEDULE = "view_personal_schedule"
    INSPECT_CLIENT_CHATS = "inspect_client_chats"
    TOGGLE_AUDIO_RECORDING = "toggle_audio_recording"


ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),  # Super Admin has all permissions
    Role.SALON_MANAGER: {
        Permission.MANAGE_RAG_WIKI,
        Permission.MANAGE_PRICING,
        Permission.MANAGE_MASTERS,
        Permission.CONFIGURE_PAYMENTS,
        Permission.VIEW_ALL_APPOINTMENTS,
        Permission.MANAGE_APPOINTMENTS,
        Permission.INSPECT_CLIENT_CHATS,
        Permission.TOGGLE_AUDIO_RECORDING,
    },
    Role.RECEPTIONIST: {
        Permission.VIEW_ALL_APPOINTMENTS,
        Permission.MANAGE_APPOINTMENTS,
        Permission.INSPECT_CLIENT_CHATS,
    },
    Role.MASTER: {
        Permission.VIEW_PERSONAL_SCHEDULE,
    },
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a given role possesses a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())
