"""
Tools for Unwind AI Assistant.

This package contains all the tools used by the agents to interact
with the Supabase database.
"""

# Data Agent Tools
from .data_tools import (
    get_today_items,
    get_week_items,
    get_items_by_category,
    get_items_by_tags,
    search_items,
    get_worries,
    get_item_details
)

# Planning Agent Tools
from .planning_tools import (
    get_user_stats,
    get_completion_history,
    count_pending_by_priority
)

# Reassurance Agent Tools
from .reassurance_tools import (
    get_spiral_items,
    get_recent_completions
)

# Shared Tools (available to all agents)
from .shared_tools import (
    mark_item_complete,
    update_item_priority,
    add_note_to_item
)

__all__ = [
    # Data tools
    'get_today_items',
    'get_week_items',
    'get_items_by_category',
    'get_items_by_tags',
    'search_items',
    'get_worries',
    'get_item_details',
    # Planning tools
    'get_user_stats',
    'get_completion_history',
    'count_pending_by_priority',
    # Reassurance tools
    'get_spiral_items',
    'get_recent_completions',
    # Shared tools
    'mark_item_complete',
    'update_item_priority',
    'add_note_to_item',
]
