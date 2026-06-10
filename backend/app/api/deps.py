"""
app/api/deps.py
===============
FastAPI dependency re-exports.

All actual dependency implementations live in app.core.security.
This module exists for backward compatibility — existing routers that import
from app.api.deps continue to work without changes.

Preferred import path for new code:
    from app.core.security import get_current_user, get_current_active_user, get_db
"""
from app.core.security import (  # noqa: F401  — re-exported for backward compat
    get_db,
    get_current_user,
    get_current_active_user,
)
