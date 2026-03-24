# utils.py
"""
utils.py
--------
Helper utilities for FASTRAN GUI.

Responsibilities:
1. Safe Type Conversion: Prevents the GUI from crashing if the user leaves 
   a numeric field empty or types non-numeric text.
2. Formatting: Standardizes how scientific notation is displayed.
"""

def safe_float(value, default=0.0):
    """
    Safely converts a string to a float.
    
    Args:
        value (str): The input string from a Tkinter Entry widget.
        default (float): The value to return if conversion fails.
        
    Returns:
        float: The converted number or the default.
    """
    if not value:
        return default
    
    # Handle strings that are just whitespace
    if isinstance(value, str) and not value.strip():
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        # This catches cases like "abc", "1.2.3", or None
        return default


def safe_int(value, default=0):
    """
    Safely converts a string to an integer.
    Handles cases like "5.0" by converting to float first.
    """
    if not value:
        return default
        
    if isinstance(value, str) and not value.strip():
        return default

    try:
        # Convert to float first to handle "1.0", then to int
        return int(float(value))
    except (ValueError, TypeError):
        return default