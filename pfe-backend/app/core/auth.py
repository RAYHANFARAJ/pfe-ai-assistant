from __future__ import annotations

"""
Keycloak JWT validation for FastAPI.

Every protected endpoint adds `Depends(require_auth)` to its signature.
The dependency fetches the Keycloak JWKS (cached for 5 min), verifies the
RS256 signature, and returns a populated `TokenData` object with the
real user's identity extracted from the token claims.

Example of a decoded Keycloak access token (tokenParsed on the frontend):
{
  "sub": "a1b2c3d4-...",          ← Keycloak user ID (stable)
  "preferred_username": "demo",
  "given_name": "Demo",
  "family_name": "User",
  "email": "demo@sellynx.com",
  "email_verified": true,
  "name": "Demo User",
  "realm_access": { "roles": ["app-user"] },
  "iss": "http://localhost:8080/realms/sellynx",
  "aud": "account",
  "exp": 1700000000,
  "iat": 1699999700
}
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# ── JWKS cache (TTL = 5 minutes) ──────────────────────────────────────────────
_jwks_cache: Dict[str, Any] = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 300  # seconds


def _jwks_url() -> str:
    # Use internal URL for fetching JWKS when running inside Docker
    # (keycloak_url may be localhost which is not reachable from inside a container)
    base = settings.keycloak_internal_url or settings.keycloak_url
    return f"{base}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"


def _issuer() -> str:
    # Must match the 'iss' claim in the token — always the public-facing URL
    return f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"


def _get_jwks() -> Dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if not _jwks_cache or now - _jwks_fetched_at > _JWKS_TTL:
        try:
            resp = httpx.get(_jwks_url(), timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_fetched_at = now
            logger.debug("JWKS refreshed from %s", _jwks_url())
        except Exception as exc:
            logger.error("Failed to fetch JWKS: %s", exc)
            if not _jwks_cache:
                raise RuntimeError(f"Cannot reach Keycloak JWKS endpoint: {exc}") from exc
    return _jwks_cache


# ── Token data ────────────────────────────────────────────────────────────────

@dataclass
class TokenData:
    sub:        str
    email:      str
    name:       str
    username:   str
    given_name: str
    family_name: str
    roles:      List[str] = field(default_factory=list)
    raw:        Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "TokenData":
        first = payload.get("given_name", "")
        last  = payload.get("family_name", "")
        return cls(
            sub         = payload.get("sub", ""),
            email       = payload.get("email", ""),
            name        = payload.get("name") or f"{first} {last}".strip() or payload.get("preferred_username", ""),
            username    = payload.get("preferred_username", ""),
            given_name  = first,
            family_name = last,
            roles       = payload.get("realm_access", {}).get("roles", []),
            raw         = payload,
        )


# ── FastAPI dependencies ──────────────────────────────────────────────────────

def _decode_token(token: str) -> Dict[str, Any]:
    """Validate signature, issuer, and expiry. Raises HTTPException on failure."""
    try:
        jwks = _get_jwks()
        payload: Dict[str, Any] = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            issuer=_issuer(),
            options={"verify_aud": False},  # public clients have no fixed audience
        )
        return payload
    except JWTError as exc:
        logger.warning("Token validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except RuntimeError as exc:
        logger.error("Auth service unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable.",
        ) from exc


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> TokenData:
    """
    FastAPI dependency — requires a valid Keycloak Bearer token.
    Usage:  user: TokenData = Depends(require_auth)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_token(credentials.credentials)
    return TokenData.from_payload(payload)


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[TokenData]:
    """
    FastAPI dependency — token is optional.
    Returns TokenData if a valid token is present, None otherwise.
    Usage:  user: Optional[TokenData] = Depends(optional_auth)
    """
    if not credentials:
        return None
    try:
        payload = _decode_token(credentials.credentials)
        return TokenData.from_payload(payload)
    except HTTPException:
        return None
