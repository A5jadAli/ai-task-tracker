def calculate_progress(status: str) -> int:
    """Calculate progress percentage from status"""
    progress_map = {
        "pending": 0,
        "git_sync": 10,
        "planning": 30,
        "awaiting_approval": 40,
        "approved": 45,
        "in_progress": 60,
        "testing": 80,
        "completed": 100,
        "failed": 0,
        "rejected": 0
    }
    # Handle status objects if passed
    status_str = getattr(status, 'value', status)
    return progress_map.get(status_str, 0)
