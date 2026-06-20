from typing import List, Dict, Any


def add_src_ids(context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"src_id": f"SRC_{i+1}", **item} for i, item in enumerate(context)]
