"""
Authing OIDC integration.
Supports: email, phone, WeChat, social logins via Authing.
Each user automatically gets a platform wallet.
"""
import logging
import os
import secrets
from datetime import timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from models.database import User
from utils.auth import create_access_token, hash_password
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

AUTHING_APP_ID = os.getenv("AUTHING_APP_ID", "69c4068689f20577ca2e411d")
AUTHING_APP_SECRET = os.getenv("AUTHING_APP_SECRET", "df67c898cb59f4b8c0fa0ff3f44b1d5f")
AUTHING_DOMAIN = os.getenv("AUTHING_DOMAIN", "https://wysqur64tc87-demo.authing.cn")
AUTHING_REDIRECT_URI = os.getenv("AUTHING_REDIRECT_URI", "https://www.nautilus.social/api/auth/authing/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.nautilus.social")


@router.get("/authing/login")
async def authing_login():
    """Redirect to Authing hosted login page."""
    state = secrets.token_urlsafe(32)

    # Store state in Redis if available
    try:
        from utils.cache import get_cache
        cache = get_cache()
        cache.set(f"authing_state:{state}", "pending", ttl=300)
    except Exception:
        pass

    auth_url = (
        f"{AUTHING_DOMAIN}/oidc/auth"
        f"?client_id={AUTHING_APP_ID}"
        f"&redirect_uri={AUTHING_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid profile email phone"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/authing/callback")
async def authing_callback(
    request: Request,
    code: str = Query(...),
    state: Optional[str] = Query(None),
):
    """Handle Authing OIDC callback. Exchange code for token, get user info."""

    # 1. Exchange code for tokens
    async with httpx.AsyncClient(timeout=15) as client:
        token_resp = await client.post(
            f"{AUTHING_DOMAIN}/oidc/token",
            data={
                "grant_type": "authorization_code",
                "client_id": AUTHING_APP_ID,
                "client_secret": AUTHING_APP_SECRET,
                "code": code,
                "redirect_uri": AUTHING_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_resp.status_code != 200:
            logger.error("Authing token exchange failed: %s", token_resp.text)
            raise HTTPException(400, "Failed to exchange code for token")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(400, "No access token from Authing")

        # 2. Get user info
        user_resp = await client.get(
            f"{AUTHING_DOMAIN}/oidc/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if user_resp.status_code != 200:
            raise HTTPException(400, "Failed to get user info from Authing")

        authing_user = user_resp.json()

    # 3. Extract user info
    authing_id = authing_user.get("sub", "")
    email = authing_user.get("email", "")
    phone = authing_user.get("phone_number", "")
    name = authing_user.get("name") or authing_user.get("nickname") or authing_user.get("preferred_username") or ""
    picture = authing_user.get("picture", "")

    logger.info("Authing user: id=%s email=%s phone=%s name=%s", authing_id, email, phone, name)

    # 4. Find or create user in our database
    db = next(get_db())
    try:
        # Try to find by email first, then by authing_id stored in external field
        user = None
        if email:
            user = db.query(User).filter(User.email == email).first()
        if not user and phone:
            user = db.query(User).filter(User.email == f"{phone}@phone.nautilus.local").first()

        if not user:
            # Create new user
            username = name or (email.split("@")[0] if email else f"user_{secrets.token_hex(4)}")
            # Ensure unique
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                username = f"{username}_{secrets.token_hex(3)}"

            user_email = email or f"{phone}@phone.nautilus.local" if phone else f"{authing_id}@authing.nautilus.local"

            user = User(
                username=username,
                email=user_email,
                hashed_password=hash_password(secrets.token_urlsafe(32)),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Created user from Authing: %s (email=%s)", username, user_email)

            # Auto-create wallet for new user
            try:
                from eth_account import Account
                acct = Account.create()
                user.wallet_address = acct.address.lower()
                db.commit()
                logger.info("Wallet created for user %s: %s", username, user.wallet_address)
            except Exception as e:
                logger.warning("Wallet creation failed for user %s: %s", username, e)

        # 5. Generate JWT
        jwt_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(days=7),
        )

        # 6. Redirect to frontend with token
        redirect_url = f"{FRONTEND_URL}/auth/callback?token={jwt_token}"
        return RedirectResponse(url=redirect_url)

    finally:
        db.close()
