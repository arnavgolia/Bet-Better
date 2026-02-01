"""
Utility functions for API responses.
"""

from typing import Any
from uuid import UUID


def uuid_to_str(value: Any) -> str:
    """Convert UUID to string, handling both UUID objects and strings."""
    if isinstance(value, UUID):
        return str(value)
    return value
