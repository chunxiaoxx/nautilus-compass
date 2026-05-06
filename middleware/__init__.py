"""Compass middleware · auth + quota (Day 7 simplified · platform_jwt only)."""
from .auth import Tenant, authenticate

__all__ = ["Tenant", "authenticate"]
