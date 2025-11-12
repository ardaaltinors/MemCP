import os
from typing import Optional

from fastmcp.server.auth.providers.github import GitHubProvider
from fastmcp.server.auth.providers.google import GoogleProvider
# from fastmcp.server.auth.providers.oidc import OIDCProvider


_AUTH_PROVIDER = None


def build_auth_provider() -> Optional[object]:
    global _AUTH_PROVIDER
    if _AUTH_PROVIDER is not None:
        return _AUTH_PROVIDER

    provider_name = (os.getenv("MCP_AUTH_PROVIDER") or "").strip().lower()
    base_url = os.getenv("MCP_BASE_URL") or f"http://{os.getenv('MCP_SERVER_HOST','127.0.0.1')}:{os.getenv('MCP_SERVER_PORT','4200')}"

    if provider_name == "google":
        cid = os.getenv("GOOGLE_CLIENT_ID")
        csec = os.getenv("GOOGLE_CLIENT_SECRET")
        if cid and csec:
            _AUTH_PROVIDER = GoogleProvider(client_id=cid, client_secret=csec, base_url=base_url)
        else:
            print("[FastMCP OAuth] GOOGLE_CLIENT_ID/SECRET not set; OAuth provider disabled")
    elif provider_name == "github":
        cid = os.getenv("GITHUB_CLIENT_ID_MCP") or os.getenv("GITHUB_CLIENT_ID")
        csec = os.getenv("GITHUB_CLIENT_SECRET_MCP") or os.getenv("GITHUB_CLIENT_SECRET")
        if cid and csec:
            _AUTH_PROVIDER = GitHubProvider(client_id=cid, client_secret=csec, base_url=base_url)
        else:
            print("[FastMCP OAuth] GITHUB_CLIENT_ID_MCP/SECRET_MCP (or GITHUB_CLIENT_ID/SECRET) not set; OAuth provider disabled")
    # elif provider_name == "oidc":
    #     issuer = os.getenv("OIDC_ISSUER")
    #     cid = os.getenv("OIDC_CLIENT_ID")
    #     csec = os.getenv("OIDC_CLIENT_SECRET")
    #     config_url = os.getenv("OIDC_CONFIG_URL")
    #     if issuer and cid and csec:
    #         _AUTH_PROVIDER = OIDCProvider(
    #             issuer=issuer,
    #             client_id=cid,
    #             client_secret=csec,
    #             base_url=base_url,
    #             configuration_url=config_url,
    #         )

    if _AUTH_PROVIDER is None and provider_name:
        print(f"[FastMCP OAuth] MCP_AUTH_PROVIDER='{provider_name}' requested but provider not initialized; falling back to no auth")
    return _AUTH_PROVIDER


def get_auth_provider() -> Optional[object]:
    return _AUTH_PROVIDER
