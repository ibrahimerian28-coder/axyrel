"""Shared SQLAlchemy declarative base for Axyrel models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all Axyrel ORM models."""
