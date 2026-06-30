"""Firebase ID-token verification for multi-tenant request scoping.

Each web request carries the caller's Firebase ID token (``Authorization: Bearer
<token>``). We verify it against Google's public keys (no service-account secret
needed — only the project id) and return the user's UID, which every data query
is scoped by.

Local dev convenience: if ``FIREBASE_PROJECT_ID`` is unset (no Firebase), token
verification is skipped and a single shared ``local-dev`` user is used, so the
app still runs fully offline.
"""
from __future__ import annotations

from fastapi import HTTPException, Request

from stockstalker.config import settings
from stockstalker.config.settings import DEV_UID
from stockstalker.utils import logger

# Google's public keys for Firebase Secure Token (rotated ~daily; PyJWKClient caches).
_FIREBASE_JWKS_URL = (
    "https://www.googleapis.com/service_accounts/v1/jwk/"
    "securetoken@system.gserviceaccount.com"
)

_jwk_client = None  # lazily built PyJWKClient (caches the keys)


def _jwks():
    global _jwk_client
    if _jwk_client is None:
        from jwt import PyJWKClient

        _jwk_client = PyJWKClient(_FIREBASE_JWKS_URL)
    return _jwk_client


def _verify_token(token: str) -> str:
    """Verify a Firebase ID token's signature + claims; return its UID."""
    import jwt

    project_id = settings.firebase_project_id
    signing_key = _jwks().get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=project_id,
        issuer=f"https://securetoken.google.com/{project_id}",
    )
    uid = claims.get("sub") or claims.get("user_id")
    if not uid:
        raise ValueError("token carries no uid")
    return str(uid)


async def get_uid(request: Request) -> str:
    """FastAPI dependency → the caller's user id (Firebase UID).

    - FIREBASE_PROJECT_ID set  → require + verify a Bearer token (401 otherwise).
    - FIREBASE_PROJECT_ID unset → return the shared DEV_UID (offline dev).
    """
    if not settings.firebase_project_id:
        return DEV_UID

    header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not header or not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")
    token = header.split(" ", 1)[1].strip()
    try:
        return _verify_token(token)
    except Exception as exc:  # noqa: BLE001 — any failure is an auth failure
        logger.warning("Token verification failed: {}", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
