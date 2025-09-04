# utils.py
"""
utils.py
--------
Contains simple, reusable utility functions used across the application,
such as safe type conversions.
"""
from typing import Any

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to a float, returning a default on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to an integer, returning a default on failure."""
    try:
        # Handle potential float strings like "1.0"
        return int(float(value))
    except (ValueError, TypeError):
        return default