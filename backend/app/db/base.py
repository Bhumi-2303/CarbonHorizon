"""
SQLAlchemy base model declaration.
All ORM models import Base from here to share the same metadata.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
