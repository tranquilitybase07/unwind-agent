"""
Data Agent Tools for Unwind AI Assistant.

These tools query the Supabase database to retrieve user's items, tasks, and worries.
All queries filter by user_id to respect Row-Level Security (RLS).

Tools:
1. get_today_items - Get items due today
2. get_week_items - Get items due this week
3. get_items_by_category - Filter items by category
4. get_items_by_tags - Filter items by tags
5. search_items - Full-text search
6. get_worries - Get all worries
7. get_item_details - Get detailed info for specific item
"""

import logging
from typing import List, Dict, Any, Optional
from shared.database import db

logger = logging.getLogger(__name__)


async def get_today_items(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all items due today for the user.

    Uses the pre-created user_today_view which includes items with:
    - status = 'pending'
    - due_date <= CURRENT_DATE
    - Ordered by final_priority_score DESC

    Args:
        user_id: UUID of the authenticated user

    Returns:
        List of items with category, tags, priority info
    """
    query = """
        SELECT
            id,
            title,
            category,
            due_date,
            due_time,
            priority,
            final_priority_score,
            tags,
            status
        FROM user_today_view
        WHERE user_id = $1
        ORDER BY final_priority_score DESC
        LIMIT 50;
    """

    try:
        items = await db.fetch_all(query, user_id, user_id=user_id)
        logger.info(f"Retrieved {len(items)} items due today for user {user_id}")
        return items
    except Exception as e:
        logger.error(f"Failed to get today's items for user {user_id}: {e}")
        return []


async def get_week_items(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all items due this week for the user.

    Uses the user_this_week_view which includes items with:
    - status = 'pending'
    - due_date between CURRENT_DATE and CURRENT_DATE + 7 days

    Args:
        user_id: UUID of the authenticated user

    Returns:
        List of items due this week
    """
    query = """
        SELECT
            id,
            title,
            category,
            due_date,
            priority,
            tags,
            status
        FROM user_this_week_view
        WHERE user_id = $1
        ORDER BY due_date ASC, priority DESC
        LIMIT 100;
    """

    try:
        items = await db.fetch_all(query, user_id, user_id=user_id)
        logger.info(f"Retrieved {len(items)} items due this week for user {user_id}")
        return items
    except Exception as e:
        logger.error(f"Failed to get this week's items for user {user_id}: {e}")
        return []


async def get_items_by_category(
    user_id: str,
    category_name: str
) -> List[Dict[str, Any]]:
    """
    Get all pending items filtered by category name.

    Categories: 'Tasks', 'Ideas', 'Errands', 'Health',
                'Relationships', 'Worries Vault', 'Recurring'

    Args:
        user_id: UUID of the authenticated user
        category_name: Name of the category to filter by

    Returns:
        List of items in the specified category
    """
    query = """
        SELECT
            i.id,
            i.title,
            i.description,
            c.name as category,
            i.due_date,
            i.due_time,
            i.priority,
            i.final_priority_score,
            ARRAY_AGG(it.tag) FILTER (WHERE it.tag IS NOT NULL) as tags,
            i.status,
            i.created_at
        FROM items i
        JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_tags it ON i.id = it.item_id
        WHERE i.user_id = $1
          AND c.name = $2
          AND i.status = 'pending'
        GROUP BY i.id, c.name
        ORDER BY i.final_priority_score DESC
        LIMIT 100;
    """

    try:
        items = await db.fetch_all(query, user_id, category_name, user_id=user_id)
        logger.info(
            f"Retrieved {len(items)} items in category '{category_name}' "
            f"for user {user_id}"
        )
        return items
    except Exception as e:
        logger.error(
            f"Failed to get items by category '{category_name}' "
            f"for user {user_id}: {e}"
        )
        return []


async def get_items_by_tags(
    user_id: str,
    tags: List[str]
) -> List[Dict[str, Any]]:
    """
    Get all pending items that match ANY of the provided tags.

    Args:
        user_id: UUID of the authenticated user
        tags: List of tag strings to filter by (e.g., ["work", "urgent"])

    Returns:
        List of items matching any of the tags
    """
    if not tags:
        logger.warning(f"No tags provided for user {user_id}")
        return []

    query = """
        SELECT DISTINCT
            i.id,
            i.title,
            i.description,
            c.name as category,
            i.due_date,
            i.priority,
            i.final_priority_score,
            ARRAY_AGG(it.tag) FILTER (WHERE it.tag IS NOT NULL) as tags,
            i.status
        FROM items i
        JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_tags it ON i.id = it.item_id
        WHERE i.user_id = $1
          AND i.id IN (
              SELECT DISTINCT item_id
              FROM item_tags
              WHERE tag = ANY($2::text[])
          )
          AND i.status = 'pending'
        GROUP BY i.id, c.name
        ORDER BY i.final_priority_score DESC
        LIMIT 100;
    """

    try:
        items = await db.fetch_all(query, user_id, tags, user_id=user_id)
        logger.info(
            f"Retrieved {len(items)} items with tags {tags} for user {user_id}"
        )
        return items
    except Exception as e:
        logger.error(f"Failed to get items by tags for user {user_id}: {e}")
        return []


async def search_items(
    user_id: str,
    search_query: str
) -> List[Dict[str, Any]]:
    """
    Full-text search in item titles and descriptions.

    Searches for the query string in both title and description fields
    (case-insensitive).

    Args:
        user_id: UUID of the authenticated user
        search_query: Search term to find

    Returns:
        List of items matching the search query
    """
    if not search_query or len(search_query.strip()) == 0:
        logger.warning(f"Empty search query for user {user_id}")
        return []

    # Add wildcards for partial matching
    search_pattern = f"%{search_query}%"

    query = """
        SELECT
            i.id,
            i.title,
            i.description,
            c.name as category,
            i.due_date,
            i.priority,
            i.final_priority_score,
            ARRAY_AGG(it.tag) FILTER (WHERE it.tag IS NOT NULL) as tags,
            i.status
        FROM items i
        JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_tags it ON i.id = it.item_id
        WHERE i.user_id = $1
          AND i.status = 'pending'
          AND (
              i.title ILIKE $2
              OR i.description ILIKE $2
          )
        GROUP BY i.id, c.name
        ORDER BY
            CASE
                WHEN i.title ILIKE $2 THEN 1  -- Title matches rank higher
                ELSE 2
            END,
            i.final_priority_score DESC
        LIMIT 50;
    """

    try:
        items = await db.fetch_all(query, user_id, search_pattern, user_id=user_id)
        logger.info(
            f"Search '{search_query}' returned {len(items)} items for user {user_id}"
        )
        return items
    except Exception as e:
        logger.error(f"Search failed for user {user_id}: {e}")
        return []


async def get_worries(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all items in the Worries Vault category.

    Uses the user_worries_vault_view which includes:
    - Items in 'Worries Vault' category
    - status = 'pending'
    - Includes is_worry_spiral and spiral_breakdown info

    Args:
        user_id: UUID of the authenticated user

    Returns:
        List of worry items with spiral information
    """
    query = """
        SELECT
            id,
            title,
            is_worry_spiral,
            spiral_breakdown,
            priority,
            tags,
            created_at
        FROM user_worries_vault_view
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 100;
    """

    try:
        worries = await db.fetch_all(query, user_id, user_id=user_id)
        logger.info(f"Retrieved {len(worries)} worries for user {user_id}")
        return worries
    except Exception as e:
        logger.error(f"Failed to get worries for user {user_id}: {e}")
        return []


async def get_item_details(
    user_id: str,
    item_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get complete details for a specific item.

    Includes all fields: title, description, category, priority,
    deadlines, tags, anxiety info, etc.

    Args:
        user_id: UUID of the authenticated user
        item_id: UUID of the item to retrieve

    Returns:
        Complete item record, or None if not found
    """
    query = """
        SELECT
            i.id,
            i.title,
            i.description,
            c.name as category,
            i.due_date,
            i.due_time,
            i.is_all_day,
            i.deadline_confidence,
            i.priority,
            i.urgency_score,
            i.importance_score,
            i.emotional_weight_score,
            i.final_priority_score,
            i.item_type,
            i.status,
            i.completed_at,
            i.is_worry_spiral,
            i.spiral_breakdown,
            i.worry_acknowledgment_text,
            i.user_notes,
            i.custom_tags,
            ARRAY_AGG(it.tag) FILTER (WHERE it.tag IS NOT NULL) as all_tags,
            i.blocked_by_item_id,
            i.parent_task_id,
            i.created_at,
            i.updated_at
        FROM items i
        JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_tags it ON i.id = it.item_id
        WHERE i.id = $1
          AND i.user_id = $2
        GROUP BY i.id, c.name;
    """

    try:
        item = await db.fetch_one(query, item_id, user_id, user_id=user_id)
        if item:
            logger.info(f"Retrieved item {item_id} for user {user_id}")
        else:
            logger.warning(f"Item {item_id} not found for user {user_id}")
        return item
    except Exception as e:
        logger.error(f"Failed to get item {item_id} for user {user_id}: {e}")
        return None
