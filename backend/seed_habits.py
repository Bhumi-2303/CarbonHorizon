"""
Standalone habit seeding script and compatibility wrapper.
"""
from __future__ import annotations

import os
import sys
from typing import Optional
from sqlalchemy.orm import Session

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from app.db.init_db import seed_habit_definitions as _seed_habit_definitions
from app.db.session import SessionLocal


def seed_habit_definitions(
    db: Optional[Session] = None, *, commit: bool = True
) -> None:
    """
    Seed habit definitions. If db is omitted, manages its own session.
    """
    if db is None:
        session = SessionLocal()
        try:
            _seed_habit_definitions(session, commit=commit)
        finally:
            session.close()
    else:
        _seed_habit_definitions(db, commit=commit)


if __name__ == "__main__":
    seed_habit_definitions()
