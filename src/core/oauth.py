import os
from typing import Dict, Optional
from urllib.parse import urljoin

from fastapi import Request
from authlib.integrations.starlette_client import OAuth


_oauth: Optional[OAuth] = None


def get_oauth() -> OAuth:
    global _oauth
    if _oauth is not None:
        return _oauth

    oauth = OAuth()

    # Google
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if google_client_id and google_client_secret:
        oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    # GitHub
    github_client_id = os.getenv("GITHUB_CLIENT_ID_ASTRO")
    github_client_secret = os.getenv("GITHUB_CLIENT_SECRET_ASTRO")
    if github_client_id and github_client_secret:
        oauth.register(
            name="github",
            client_id=github_client_id,
            client_secret=github_client_secret,
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "read:user user:email"},
        )

    _oauth = oauth
    return oauth


def get_callback_url(provider: str) -> str:
    # Always point the provider back to the backend callback
    base = os.getenv("OAUTH_REDIRECT_BASE_URL") or "http://localhost:8000"
    return urljoin(base if base.endswith("/") else base + "/", f"auth/oauth/{provider}/callback")


def list_providers() -> Dict[str, bool]:
    oauth = get_oauth()
    return {name: True for name in oauth._clients.keys()}
