"""
Reassurance Agent Tools for Unwind AI Assistant.

These tools help provide evidence-based compassionate support by:
- Identifying worry spirals
- Referencing actual completion history

Tools:
1. get_spiral_items - Get items marked as worry spirals
2. get_recent_completions - Recent wins to reference for reassurance
"""

import logging
from typing import List, Dict, Any
from shared.database import db

logger = logging.getLogger(__name__)


async def get_spiral_items(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all items marked as worry spirals.

    A worry spiral is detected when AI identifies catastrophizing patterns
    like "what if X → Y → Z" chains.

    The spiral_breakdown field contains structured analysis of the spiral,
    useful for providing targeted reassurance.

    Args:
        user_id: UUID of the authenticated user

    Returns:
        List of worry spiral items with breakdown info
    """
    query = """
        SELECT
            id,
            title,
            description,
            spiral_breakdown,
            worry_acknowledgment_text,
            priority,
            created_at,
            updated_at
        FROM items
        WHERE user_id = $1
          AND is_worry_spiral = true
          AND status = 'pending'
        ORDER BY created_at DESC
        LIMIT 50;
    """

    try:
        spirals = await db.fetch_all(query, user_id, user_id=user_id)
        logger.info(f"Retrieved {len(spirals)} worry spirals for user {user_id}")
        return spirals
    except Exception as e:
        logger.error(f"Failed to get spiral items for user {user_id}: {e}")
        return []


async def get_recent_completions(
    user_id: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get recently completed items to reference for reassurance.

    This provides evidence-based reassurance by showing the user's
    actual track record of completing tasks.

    Includes mood information to highlight positive outcomes.

    Args:
        user_id: UUID of the authenticated user
        limit: Maximum number of completions to return (default: 5)

    Returns:
        List of recently completed items with titles and mood info
    """
    query = """
        SELECT
            i.id,
            i.title,
            i.completed_at,
            i.completion_time_minutes,
            i.user_mood_after_completion as mood_after,
            c.name as category,
            cl.user_mood_before as mood_before,
            cl.was_procrastinated
        FROM items i
        JOIN categories c ON i.category_id = c.id
        LEFT JOIN completions_log cl ON i.id = cl.item_id
        WHERE i.user_id = $1
          AND i.status = 'completed'
        ORDER BY i.completed_at DESC
        LIMIT $2;
    """

    try:
        completions = await db.fetch_all(query, user_id, limit, user_id=user_id)
        logger.info(
            f"Retrieved {len(completions)} recent completions for user {user_id}"
        )
        return completions
    except Exception as e:
        logger.error(f"Failed to get recent completions for user {user_id}: {e}")
        return []
