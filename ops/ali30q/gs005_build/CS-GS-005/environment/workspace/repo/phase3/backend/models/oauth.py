"""
OAuth 2.0 database models for Nautilus.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OAuthClient(Base):
    """OAuth client (third-party application) model."""
    __tablename__ = "oauth_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, nullable=False, index=True)
    client_secret = Column(String(128), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    redirect_uris = Column(JSON, nullable=False)  # List of allowed redirect URIs
    logo_url = Column(String(500))
    website = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class OAuthAuthorizationCode(Base):
    """OAuth authorization code model."""
    __tablename__ = "oauth_authorization_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    client_id = Column(String(64), nullable=False, index=True)
    agent_address = Column(String(42), nullable=False, index=True)
    redirect_uri = Column(String(500), nullable=False)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class OAuthAccessToken(Base):
    """OAuth access token model."""
    __tablename__ = "oauth_access_tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String(64), unique=True, nullable=False, index=True)
    refresh_token = Column(String(64), unique=True, nullable=False, index=True)
    client_id = Column(String(64), nullable=False, index=True)
    agent_address = Column(String(42), nullable=False, index=True)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False, index=True)
    refresh_expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime)
