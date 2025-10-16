"""Therapeutic activities for psychedelic integration."""

from integro.activities.base import BaseActivity, ActivityState
from integro.activities.daily_content import DailyContentActivity
from integro.activities.ifs import IFSActivity

# Activity factory for easy instantiation
ACTIVITIES = {
    "daily_content": DailyContentActivity,
    "ifs": IFSActivity
}

def get_activity(activity_name: str) -> BaseActivity:
    """
    Get an activity instance by name.
    
    Args:
        activity_name: Name of the activity
        
    Returns:
        Activity instance
        
    Raises:
        ValueError: If activity not found
    """
    if activity_name not in ACTIVITIES:
        raise ValueError(f"Unknown activity: {activity_name}")
    
    return ACTIVITIES[activity_name]()

__all__ = [
    "BaseActivity",
    "ActivityState",
    "DailyContentActivity",
    "IFSActivity",
    "get_activity",
    "ACTIVITIES"
]