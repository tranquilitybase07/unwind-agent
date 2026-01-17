"""
Database connection layer for Unwind AI Assistant.

Provides async PostgreSQL connection to Supabase with:
- Connection pooling
- RLS-aware queries (always filter by user_id)
- Error handling and logging
"""

import os
import logging
from typing import Optional, List, Dict, Any
import asyncpg
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class Database:
    """
    Async PostgreSQL database connection manager for Supabase.

    Handles connection pooling and provides helper methods for querying
    with automatic user_id filtering to respect Row-Level Security (RLS).
    """

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._host = os.getenv('SUPABASE_DB_HOST')
        self._port = int(os.getenv('SUPABASE_DB_PORT', '5432'))
        self._database = os.getenv('SUPABASE_DB_NAME', 'postgres')
        self._user = os.getenv('SUPABASE_DB_USER', 'postgres')
        self._password = os.getenv('SUPABASE_DB_PASSWORD')
        self._min_size = int(os.getenv('DB_POOL_MIN_SIZE', '1'))
        self._max_size = int(os.getenv('DB_POOL_MAX_SIZE', '10'))

    async def connect(self):
        """Initialize the connection pool."""
        if self.pool is not None:
            logger.warning("Database pool already exists. Skipping connection.")
            return

        if not all([self._host, self._password]):
            raise ValueError(
                "Missing required database credentials. "
                "Please set SUPABASE_DB_HOST and SUPABASE_DB_PASSWORD"
            )

        try:
            self.pool = await asyncpg.create_pool(
                host=self._host,
                port=self._port,
                database=self._database,
                user=self._user,
                password=self._password,
                min_size=self._min_size,
                max_size=self._max_size,
                command_timeout=60  # 60 second timeout for queries
            )
            logger.info(
                f"Database pool created: {self._host}:{self._port}/{self._database} "
                f"(pool size: {self._min_size}-{self._max_size})"
            )
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self):
        """Close the connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("Database pool closed")

    @asynccontextmanager
    async def acquire(self):
        """
        Context manager to acquire a connection from the pool.

        Usage:
            async with db.acquire() as conn:
                result = await conn.fetch("SELECT * FROM items WHERE id = $1", item_id)
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as connection:
            yield connection

    async def fetch_one(
        self,
        query: str,
        *args,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return a single row as a dictionary.

        Args:
            query: SQL query string
            *args: Query parameters
            user_id: User ID for RLS filtering (recommended to pass explicitly)

        Returns:
            Dictionary with column names as keys, or None if no rows found
        """
        async with self.acquire() as conn:
            try:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"Query failed: {query[:100]}... Error: {e}")
                raise

    async def fetch_all(
        self,
        query: str,
        *args,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return all rows as list of dictionaries.

        Args:
            query: SQL query string
            *args: Query parameters
            user_id: User ID for RLS filtering (recommended to pass explicitly)

        Returns:
            List of dictionaries with column names as keys
        """
        async with self.acquire() as conn:
            try:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Query failed: {query[:100]}... Error: {e}")
                raise

    async def execute(
        self,
        query: str,
        *args,
        user_id: Optional[str] = None
    ) -> str:
        """
        Execute a query (INSERT, UPDATE, DELETE) and return the result status.

        Args:
            query: SQL query string
            *args: Query parameters
            user_id: User ID for RLS filtering (recommended to pass explicitly)

        Returns:
            Query result status (e.g., "UPDATE 1")
        """
        async with self.acquire() as conn:
            try:
                result = await conn.execute(query, *args)
                return result
            except Exception as e:
                logger.error(f"Query failed: {query[:100]}... Error: {e}")
                raise

    async def execute_returning(
        self,
        query: str,
        *args,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a query with RETURNING clause and get the returned row.

        Useful for INSERT/UPDATE queries that return the affected row.

        Args:
            query: SQL query string with RETURNING clause
            *args: Query parameters
            user_id: User ID for RLS filtering

        Returns:
            Dictionary with returned row, or None
        """
        async with self.acquire() as conn:
            try:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"Query failed: {query[:100]}... Error: {e}")
                raise


# Global database instance
db = Database()


# Helper function to ensure database is initialized
async def init_database():
    """Initialize the global database connection pool."""
    await db.connect()


# Helper function to cleanup database
async def cleanup_database():
    """Close the global database connection pool."""
    await db.disconnect()
