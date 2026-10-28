"""
Authentication utilities for JWT and API Key.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
import secrets

from models.database import User, APIKey, Agent
from utils.database import get_db
from monitoring_config import record_api_key_usage, record_security_event

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "86400"))  # 24 hours

# Validate JWT_SECRET at module load time
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required and must be set")
if len(JWT_SECRET) < 32:
    raise ValueError("JWT_SECRET must be at least 32 characters long for security")
if JWT_SECRET in ["your-secret-key-change-in-production", "secret", "changeme", "test"]:
    raise ValueError("JWT_SECRET cannot use default or weak values")

# HTTP Bearer for JWT
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Convert to bytes and truncate to 72 bytes for bcrypt
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(seconds=JWT_EXPIRATION)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_api_key() -> str:
    """Generate a random API key."""
    prefix = os.getenv("API_KEY_PREFIX", "nau_")
    key_length = int(os.getenv("API_KEY_LENGTH", "32"))
    random_part = secrets.token_hex(key_length)
    return f"{prefix}{random_part}"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token.

    Usage:
        @app.get("/me")
        def read_current_user(current_user: User = Depends(get_current_user)):
            return current_user
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        # 记录权限拒绝
        record_security_event(
            event_type="permission_denied",
            severity="warning",
            details={"username": username, "reason": "inactive_user"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Agent:
    """
    Get current agent from API key.

    Usage:
        @app.post("/tasks/{task_id}/accept")
        def accept_task(
            task_id: int,
            current_agent: Agent = Depends(get_current_agent)
        ):
            # Accept task logic
            pass
    """
    api_key = credentials.credentials

    # Check if it's an API key (starts with prefix)
    prefix = os.getenv("API_KEY_PREFIX", "nau_")
    if not api_key.startswith(prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    # Query API key
    api_key_obj = db.query(APIKey).filter(APIKey.key == api_key).first()
    if api_key_obj is None:
        # 记录无效的 API Key 使用
        record_api_key_usage(api_key_id="unknown", valid=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not api_key_obj.is_active:
        # 记录无效的 API Key 使用
        record_api_key_usage(api_key_id=api_key_obj.agent_id, valid=False)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive API key",
        )

    # 记录有效的 API Key 使用
    record_api_key_usage(api_key_id=api_key_obj.agent_id, valid=True)

    # Update last used timestamp
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    db.commit()

    # Get agent
    agent = db.query(Agent).filter(Agent.agent_id == api_key_obj.agent_id).first()
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return agent


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current admin user.

    Usage:
        @app.delete("/users/{user_id}")
        def delete_user(
            user_id: int,
            current_admin: User = Depends(get_current_admin_user)
        ):
            # Delete user logic
            pass
    """
    if not current_user.is_admin:
        # 记录权限拒绝
        record_security_event(
            event_type="permission_denied",
            severity="warning",
            details={"username": current_user.username, "reason": "not_admin"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return current_user


async def get_current_user_or_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> tuple[Optional[User], Optional[Agent]]:
    """
    Get current user or agent from JWT token or API key.

    This function supports both authentication methods:
    - JWT token: Returns (User, Agent) where Agent is the user's agent if exists
    - API key: Returns (None, Agent)

    Usage:
        @app.post("/tasks/{task_id}/accept")
        async def accept_task(
            task_id: int,
            auth: tuple = Depends(get_current_user_or_agent)
        ):
            user, agent = auth
            # Use agent for task operations
    """
    token = credentials.credentials
    prefix = os.getenv("API_KEY_PREFIX", "nau_")

    # Check if it's an API key
    if token.startswith(prefix):
        # API Key authentication
        api_key_obj = db.query(APIKey).filter(APIKey.key == token).first()
        if api_key_obj is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        if not api_key_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive API key",
            )

        # Update last used timestamp
        api_key_obj.last_used_at = datetime.now(timezone.utc)
        db.commit()

        # Get agent
        agent = db.query(Agent).filter(Agent.agent_id == api_key_obj.agent_id).first()
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        return (None, agent)

    else:
        # JWT token authentication
        try:
            payload = decode_access_token(token)
            username: str = payload.get("sub")

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )

            user = db.query(User).filter(User.username == username).first()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user",
                )

            # Get user's agent if exists
            agent = db.query(Agent).filter(Agent.owner == user.wallet_address).first()

            return (user, agent)

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
