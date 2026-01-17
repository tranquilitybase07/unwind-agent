"""
Planning Agent Tools for Unwind AI Assistant.

These tools analyze user's capacity, anxiety patterns, and completion history
to help with realistic daily planning.

Tools:
1. get_user_stats - Get user profile and completion patterns
2. get_completion_history - Recent completion patterns
3. count_pending_by_priority - Count pending items by priority level
"""

import logging
from typing import Dict, Any, Optional
from src.shared.database import db

logger = logging.getLogger(__name__)


async def get_user_stats(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's anxiety type and completion statistics.

    This helps the Planning Agent understand:
    - User's anxiety type ('racing_thoughts', 'intrusive_worries', 'overwhelmed')
    - How many reminders they prefer per day
    - Total items created vs completed
    - Current pending count

    Args:
        user_id: UUID of the authenticated user

    Returns:
        Dictionary with user profile and stats, or None if user not found
    """
    query = """
        SELECT
            u.anxiety_type,
            u.max_reminders_per_day,
            u.total_items,
            u.total_dumps,
            COUNT(CASE WHEN i.status = 'completed' THEN 1 END)::int as completed_count,
            COUNT(CASE WHEN i.status = 'pending' THEN 1 END)::int as pending_count,
            COUNT(CASE WHEN i.status = 'archived' THEN 1 END)::int as archived_count,
            ROUND(
                100.0 * COUNT(CASE WHEN i.status = 'completed' THEN 1 END) /
                NULLIF(COUNT(*), 0),
                2
            ) as completion_rate_percent
        FROM users u
        LEFT JOIN items i ON u.id = i.user_id
        WHERE u.id = $1
        GROUP BY u.id;
    """

    try:
        stats = await db.fetch_one(query, user_id, user_id=user_id)
        if stats:
            logger.info(f"Retrieved stats for user {user_id}: {stats['anxiety_type']}")
        else:
            logger.warning(f"User {user_id} not found")
        return stats
    except Exception as e:
        logger.error(f"Failed to get user stats for {user_id}: {e}")
        return None


async def get_completion_history(
    user_id: str,
    days: int = 7
) -> list[Dict[str, Any]]:
    """
    Get recent completion patterns for the last N days.

    Analyzes:
    - How many items completed per day
    - Average completion time
    - Mood trends (how often user felt better after completing)

    This helps the Planning Agent understand realistic daily capacity.

    Args:
        user_id: UUID of the authenticated user
        days: Number of days to look back (default: 7)

    Returns:
        List of daily completion stats
    """
    query = """
        SELECT
            DATE(completed_at) as date,
            COUNT(*)::int as completed_count,
            ROUND(AVG(completion_time_minutes), 1) as avg_time_minutes,
            COUNT(CASE WHEN user_mood_after = 'better' THEN 1 END)::int as felt_better_count,
            COUNT(CASE WHEN user_mood_after = 'worse' THEN 1 END)::int as felt_worse_count
        FROM completions_log
        WHERE user_id = $1
          AND completed_at >= CURRENT_DATE - INTERVAL '1 day' * $2
        GROUP BY DATE(completed_at)
        ORDER BY date DESC;
    """

    try:
        history = await db.fetch_all(query, user_id, days, user_id=user_id)
        logger.info(
            f"Retrieved {len(history)} days of completion history for user {user_id}"
        )
        return history
    except Exception as e:
        logger.error(f"Failed to get completion history for user {user_id}: {e}")
        return []


async def count_pending_by_priority(user_id: str) -> Dict[str, int]:
    """
    Count how many pending items the user has at each priority level.

    Returns counts for:
    - high priority
    - medium priority
    - low priority

    This helps the Planning Agent understand the current workload distribution.

    Args:
        user_id: UUID of the authenticated user

    Returns:
        Dictionary with counts by priority level
    """
    query = """
        SELECT
            priority,
            COUNT(*)::int as count
        FROM items
        WHERE user_id = $1
          AND status = 'pending'
        GROUP BY priority;
    """

    try:
        rows = await db.fetch_all(query, user_id, user_id=user_id)

        # Convert list of rows to dictionary
        counts = {
            'high': 0,
            'medium': 0,
            'low': 0,
            'total': 0
        }

        for row in rows:
            priority = row['priority']
            count = row['count']
            if priority in counts:
                counts[priority] = count
                counts['total'] += count

        logger.info(
            f"Pending items for user {user_id}: "
            f"high={counts['high']}, medium={counts['medium']}, low={counts['low']}"
        )
        return counts
    except Exception as e:
        logger.error(f"Failed to count pending items for user {user_id}: {e}")
        return {'high': 0, 'medium': 0, 'low': 0, 'total': 0}
