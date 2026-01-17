"""
Shared Tools for Unwind AI Assistant.

These tools are available to ALL agents for item management operations.

Tools:
1. mark_item_complete - Mark an item as completed
2. update_item_priority - Change item priority
3. add_note_to_item - Add user notes to an item
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from src.shared.database import db

logger = logging.getLogger(__name__)


async def mark_item_complete(
    user_id: str,
    item_id: str
) -> Dict[str, Any]:
    """
    Mark an item as completed.

    Updates:
    - status to 'completed'
    - completed_at to current timestamp

    Args:
        user_id: UUID of the authenticated user
        item_id: UUID of the item to mark complete

    Returns:
        Dictionary with success status and item_id if successful
    """
    query = """
        UPDATE items
        SET
            status = 'completed',
            completed_at = NOW(),
            updated_at = NOW()
        WHERE id = $1
          AND user_id = $2
          AND status = 'pending'
        RETURNING id, title;
    """

    try:
        result = await db.execute_returning(query, item_id, user_id, user_id=user_id)

        if result:
            logger.info(f"Marked item {item_id} as completed for user {user_id}")
            return {
                'success': True,
                'item_id': result['id'],
                'title': result['title'],
                'message': f"Item '{result['title']}' marked as completed"
            }
        else:
            logger.warning(
                f"Failed to mark item {item_id} as completed for user {user_id}. "
                "Item may not exist or already be completed."
            )
            return {
                'success': False,
                'item_id': item_id,
                'message': 'Item not found or already completed'
            }

    except Exception as e:
        logger.error(
            f"Error marking item {item_id} complete for user {user_id}: {e}"
        )
        return {
            'success': False,
            'item_id': item_id,
            'message': f'Error: {str(e)}'
        }


async def update_item_priority(
    user_id: str,
    item_id: str,
    new_priority: str
) -> Dict[str, Any]:
    """
    Update the priority of an item.

    Args:
        user_id: UUID of the authenticated user
        item_id: UUID of the item to update
        new_priority: New priority level ('high', 'medium', 'low')

    Returns:
        Dictionary with success status and updated item info
    """
    # Validate priority value
    valid_priorities = ['high', 'medium', 'low']
    if new_priority not in valid_priorities:
        return {
            'success': False,
            'item_id': item_id,
            'message': f"Invalid priority '{new_priority}'. Must be one of: {valid_priorities}"
        }

    query = """
        UPDATE items
        SET
            priority = $3,
            user_edited = true,
            updated_at = NOW()
        WHERE id = $1
          AND user_id = $2
        RETURNING id, title, priority;
    """

    try:
        result = await db.execute_returning(
            query,
            item_id,
            user_id,
            new_priority,
            user_id=user_id
        )

        if result:
            logger.info(
                f"Updated item {item_id} priority to '{new_priority}' "
                f"for user {user_id}"
            )
            return {
                'success': True,
                'item_id': result['id'],
                'title': result['title'],
                'new_priority': result['priority'],
                'message': f"Priority updated to '{new_priority}'"
            }
        else:
            logger.warning(
                f"Failed to update priority for item {item_id} "
                f"for user {user_id}. Item may not exist."
            )
            return {
                'success': False,
                'item_id': item_id,
                'message': 'Item not found'
            }

    except Exception as e:
        logger.error(
            f"Error updating priority for item {item_id} "
            f"for user {user_id}: {e}"
        )
        return {
            'success': False,
            'item_id': item_id,
            'message': f'Error: {str(e)}'
        }


async def add_note_to_item(
    user_id: str,
    item_id: str,
    note: str
) -> Dict[str, Any]:
    """
    Add a user note to an item.

    Notes are appended to the existing user_notes field,
    separated by newlines.

    Args:
        user_id: UUID of the authenticated user
        item_id: UUID of the item to add note to
        note: Note text to add

    Returns:
        Dictionary with success status
    """
    if not note or len(note.strip()) == 0:
        return {
            'success': False,
            'item_id': item_id,
            'message': 'Note cannot be empty'
        }

    # Trim and format note with timestamp
    formatted_note = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note.strip()}"

    query = """
        UPDATE items
        SET
            user_notes = CASE
                WHEN user_notes IS NULL OR user_notes = ''
                THEN $3
                ELSE user_notes || E'\\n' || $3
            END,
            user_edited = true,
            updated_at = NOW()
        WHERE id = $1
          AND user_id = $2
        RETURNING id, title, user_notes;
    """

    try:
        result = await db.execute_returning(
            query,
            item_id,
            user_id,
            formatted_note,
            user_id=user_id
        )

        if result:
            logger.info(f"Added note to item {item_id} for user {user_id}")
            return {
                'success': True,
                'item_id': result['id'],
                'title': result['title'],
                'message': 'Note added successfully'
            }
        else:
            logger.warning(
                f"Failed to add note to item {item_id} for user {user_id}. "
                "Item may not exist."
            )
            return {
                'success': False,
                'item_id': item_id,
                'message': 'Item not found'
            }

    except Exception as e:
        logger.error(
            f"Error adding note to item {item_id} for user {user_id}: {e}"
        )
        return {
            'success': False,
            'item_id': item_id,
            'message': f'Error: {str(e)}'
        }
