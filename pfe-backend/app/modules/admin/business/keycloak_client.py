from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_ADMIN_ROLE = "admin"


class KeycloakAdminService:
    """
    Thin wrapper around the Keycloak Admin REST API.
    Used to list users, assign/remove the 'admin' role.
    """

    def __init__(self) -> None:
        base = settings.keycloak_internal_url or settings.keycloak_url
        self._base      = f"{base}/admin/realms/{settings.keycloak_realm}"
        self._token_url = f"{base}/realms/master/protocol/openid-connect/token"
        self._user      = settings.keycloak_admin_user
        self._password  = settings.keycloak_admin_password
        self._client    = httpx.Client(timeout=10)

    # ── Admin token ───────────────────────────────────────────────────────────

    def _admin_token(self) -> str:
        resp = self._client.post(self._token_url, data={
            "grant_type": "password",
            "client_id":  "admin-cli",
            "username":   self._user,
            "password":   self._password,
        })
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._admin_token()}"}

    # ── Users ─────────────────────────────────────────────────────────────────

    def list_users(self) -> List[Dict[str, Any]]:
        resp = self._client.get(
            f"{self._base}/users",
            params={"max": 200},
            headers=self._headers(),
        )
        resp.raise_for_status()
        users = resp.json()
        # Attach role info to each user
        result = []
        for u in users:
            roles = self._user_realm_roles(u["id"])
            result.append({
                "id":        u["id"],
                "username":  u.get("username"),
                "email":     u.get("email", ""),
                "firstName": u.get("firstName", ""),
                "lastName":  u.get("lastName", ""),
                "enabled":   u.get("enabled", True),
                "is_admin":  _ADMIN_ROLE in roles,
                "roles":     roles,
            })
        return result

    def _user_realm_roles(self, user_id: str) -> List[str]:
        resp = self._client.get(
            f"{self._base}/users/{user_id}/role-mappings/realm",
            headers=self._headers(),
        )
        if resp.status_code != 200:
            return []
        return [r["name"] for r in resp.json()]

    # ── Role management ───────────────────────────────────────────────────────

    def _get_role(self, role_name: str) -> Optional[Dict[str, Any]]:
        resp = self._client.get(
            f"{self._base}/roles/{role_name}",
            headers=self._headers(),
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def _ensure_role_exists(self) -> Dict[str, Any]:
        role = self._get_role(_ADMIN_ROLE)
        if role:
            return role
        # Create the role
        self._client.post(
            f"{self._base}/roles",
            json={"name": _ADMIN_ROLE, "description": "Backoffice admin access"},
            headers=self._headers(),
        ).raise_for_status()
        return self._get_role(_ADMIN_ROLE)

    def assign_admin(self, user_id: str) -> None:
        role = self._ensure_role_exists()
        self._client.post(
            f"{self._base}/users/{user_id}/role-mappings/realm",
            json=[role],
            headers=self._headers(),
        ).raise_for_status()
        logger.info("Admin role assigned to user %s", user_id)

    def remove_admin(self, user_id: str) -> None:
        role = self._get_role(_ADMIN_ROLE)
        if not role:
            return
        self._client.request(
            "DELETE",
            f"{self._base}/users/{user_id}/role-mappings/realm",
            json=[role],
            headers=self._headers(),
        ).raise_for_status()
        logger.info("Admin role removed from user %s", user_id)
