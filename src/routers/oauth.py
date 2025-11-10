from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.oauth import get_oauth, get_callback_url, list_providers
from src.db.database import get_async_db
from src.crud import crud_oauth, crud_user
from src.core import security
from src.exceptions.handlers import ExceptionHandler
from src.exceptions import ExternalServiceError, InvalidCredentialsError, InactiveUserError


router = APIRouter(prefix="/auth/oauth", tags=["OAuth"])


@router.get("/providers")
async def providers():
    return {"providers": list_providers()}


@router.get("/{provider}/authorize")
async def oauth_authorize(provider: str, request: Request):
    oauth = get_oauth()
    if provider not in oauth._clients:
        raise HTTPException(status_code=404, detail="Provider not configured")
    # Persist frontend redirect if provided
    frontend_redirect = request.query_params.get("redirect_uri")
    if frontend_redirect is not None:
        try:
            request.session["frontend_redirect_uri"] = frontend_redirect
        except Exception:
            pass
    redirect_uri = get_callback_url(provider)
    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: AsyncSession = Depends(get_async_db)):
    oauth = get_oauth()
    if provider not in oauth._clients:
        raise HTTPException(status_code=404, detail="Provider not configured")

    client = oauth.create_client(provider)
    try:
        token = await client.authorize_access_token(request)
    except Exception as e:
        return ExceptionHandler.to_json_response(
            ExternalServiceError(
                message="OAuth token exchange failed",
                service_name=provider,
                original_exception=e,
            )
        )

    # Fetch user info depending on provider
    try:
        if provider == "google":
            userinfo = await client.parse_id_token(request, token)
            email = userinfo.get("email")
            subject = userinfo.get("sub")
            username_hint = userinfo.get("given_name") or email.split("@")[0]
            expires = token.get("expires_at")
        elif provider == "github":
            # Get primary email
            resp = await client.get("user", token=token)
            profile = resp.json()
            subject = str(profile.get("id"))
            username_hint = profile.get("login")
            email = profile.get("email")
            if not email:
                emails_resp = await client.get("user/emails", token=token)
                emails_list = emails_resp.json()
                primary = next((e for e in emails_list if e.get("primary") and e.get("verified")), None)
                email = primary.get("email") if primary else None
            # Authlib sets 'expires_at' under 'expires_at' or 'expires_in'
            expires = token.get("expires_at")
        else:
            raise ExternalServiceError(message="Unsupported provider", service_name=provider)
    except Exception as e:
        return ExceptionHandler.to_json_response(
            ExternalServiceError(
                message="Failed to fetch user profile from provider",
                service_name=provider,
                original_exception=e,
            )
        )

    # Upsert user and link account
    user = await crud_oauth.get_or_create_user_for_oauth(
        db,
        provider=provider,
        subject=subject,
        email=email,
        username_hint=username_hint,
    )

    # Basic active check
    if not crud_user.is_user_active(user):
        raise InactiveUserError(user_id=str(user.id), username=user.username)

    expires_at = None
    if isinstance(expires, (int, float)):
        expires_at = datetime.fromtimestamp(expires, tz=timezone.utc)

    await crud_oauth.link_oauth_account(
        db,
        user=user,
        provider=provider,
        subject=subject,
        email=email,
        access_token=token.get("access_token"),
        refresh_token=token.get("refresh_token"),
        expires_at=expires_at,
    )

    # Issue our own access token for APIs/MCP
    from datetime import timedelta
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = datetime.now(timezone.utc) + access_token_expires
    access_token = security.create_access_token(subject=user.username, expires_delta=access_token_expires)

    # If this looks like a browser flow, redirect back to frontend with token fragment
    redirect_uri = request.query_params.get("redirect_uri") or request.session.get("frontend_redirect_uri") if hasattr(request, 'session') else None
    accept = request.headers.get("accept", "")
    if redirect_uri or ("text/html" in accept):
        from urllib.parse import urlencode
        target = (redirect_uri or "/").rstrip("/")
        fragment = urlencode({
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat(),
        })
        return RedirectResponse(url=f"{target}#{fragment}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
        },
    }
