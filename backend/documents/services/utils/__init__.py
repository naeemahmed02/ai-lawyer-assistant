from typing import Any
from datetime import datetime, date

def make_json_safe(obj: Any):
    """
    Recursively convert objects into JSON-safe format.
    Fixes PageItem, numpy, tensors, etc.
    """

    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, list):
        return [make_json_safe(i) for i in obj]

    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    # fallback for objects like PageItem
    return str(obj)