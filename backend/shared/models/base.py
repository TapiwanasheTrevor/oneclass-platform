"""Compatibility export for service modules that expect shared.models.base."""

from shared.database import Base

__all__ = ["Base"]
