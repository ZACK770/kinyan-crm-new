"""
Google OAuth service — handles the Google Sign-In flow.
Uses httpx (already a project dependency) to call Google APIs directly.
Available system-wide via: from services.google_auth import ...
"""
from typing import Optional
import httpx
from db import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def _get_redirect_uri(request_origin: Optional[str] = None) -> str:
    """Get the correct redirect URI. If GOOGLE_REDIRECT_URI is explicitly set
    (not the default localhost), use it. Otherwise try to auto-detect from
    RENDER_EXTERNAL_URL or request origin."""
    import os
    uri = settings.GOOGLE_REDIRECT_URI
    # If it's still the default localhost and we're on Render, auto-fix
    if "localhost" in uri:
        render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
        if render_url:
            uri = f"{render_url}/auth/google/callback"
        elif request_origin and "localhost" not in request_origin:
            uri = f"{request_origin}/auth/google/callback"
    return uri


def get_google_login_url(state: Optional[str] = None, request_origin: Optional[str] = None) -> str:
    """Build the Google OAuth consent screen URL."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": _get_redirect_uri(request_origin),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{qs}"


async def exchange_code_for_tokens(code: str, request_origin: Optional[str] = None) -> dict:
    """Exchange the authorization code for Google tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": _get_redirect_uri(request_origin),
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_google_user_info(access_token: str) -> dict:
    """Fetch user profile from Google using the access token.
    Returns: { id, email, name, picture, ... }
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def verify_google_id_token(id_token: str) -> Optional[dict]:
    """Verify a Google ID token via Google's tokeninfo endpoint.
    Alternative lightweight verification without requiring google-auth library.
    Returns user info dict or None if invalid.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        # Verify audience matches our client ID
        if data.get("aud") != settings.GOOGLE_CLIENT_ID:
            return None
        return data
