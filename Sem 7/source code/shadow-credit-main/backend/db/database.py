"""
Async SQLite connection manager for Shadow Credit.

Production-grade database layer using raw aiosqlite — no ORM.
WAL journal mode for concurrent reads, foreign keys enforced on every
connection, schema auto-initialization on startup.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

import aiosqlite

logger = logging.getLogger(__name__)

# ── Path constants ───────────────────────────────────────────────────────────

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# ── Custom exception ────────────────────────────────────────────────────────


class DatabaseError(Exception):
    """Wraps all aiosqlite failures with original exception chained."""


# ── Schema initialization ───────────────────────────────────────────────────


async def executescript_file(db: aiosqlite.Connection, sql_path: str) -> None:
    """Read a SQL file from disk and execute it as a script.

    Used for schema initialization and migrations.

    Args:
        db: Active aiosqlite connection.
        sql_path: Absolute or relative path to the .sql file.

    Raises:
        DatabaseError: If the file cannot be read or the SQL fails.
    """
    path = Path(sql_path)
    try:
        sql = path.read_text(encoding="utf-8")
        await db.executescript(sql)
    except FileNotFoundError as exc:
        raise DatabaseError(
            f"SQL file not found: {path.resolve()}"
        ) from exc
    except aiosqlite.Error as exc:
        raise DatabaseError(
            f"Failed to execute SQL script: {path.name}"
        ) from exc


async def init_db(db_path: str) -> None:
    """Initialize the database: create directory, apply schema.

    Called once at application startup via the FastAPI lifespan hook.

    Args:
        db_path: Filesystem path to the SQLite database file.

    Raises:
        DatabaseError: If directory creation or schema init fails.
    """
    db_file = Path(db_path)

    try:
        db_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DatabaseError(
            f"Cannot create database directory: {db_file.parent}"
        ) from exc

    try:
        async with aiosqlite.connect(str(db_file)) as db:
            # WAL mode persists across connections once set
            await db.execute("PRAGMA journal_mode = WAL")
            await db.execute("PRAGMA foreign_keys = ON")
            await executescript_file(db, str(_SCHEMA_PATH))
            logger.info("Database initialized at %s", db_file.resolve())
    except aiosqlite.Error as exc:
        raise DatabaseError("Database initialization failed") from exc


# ── Connection context manager ──────────────────────────────────────────────


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Yield an aiosqlite connection with WAL mode and foreign keys enabled.

    Usage::

        async with get_db() as db:
            rows = await execute_query(db, "SELECT * FROM sessions")

    The caller does NOT need to commit reads — only writes require explicit
    commit, which ``execute_write`` handles automatically.

    Raises:
        DatabaseError: If the connection cannot be established.
    """
    # Import lazily to avoid circular dependency at module load time.
    try:
        try:
            from backend.config import get_settings
        except ModuleNotFoundError:
            from config import get_settings
        db_path = get_settings().DATABASE_PATH
    except (ImportError, AttributeError):
        # Fallback for standalone usage / testing before config exists
        db_path = str(Path(__file__).resolve().parents[2] / "data" / "shadow_credit.db")
        logger.warning("Config not available — using fallback DB path: %s", db_path)

    # Ensure parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        db = await aiosqlite.connect(db_path)
    except aiosqlite.Error as exc:
        raise DatabaseError(f"Cannot connect to database: {db_path}") from exc

    try:
        # Row factory for dict-style access
        db.row_factory = aiosqlite.Row

        # Enforce foreign keys on every connection (SQLite requires this per-connection)
        await db.execute("PRAGMA foreign_keys = ON")

        yield db
    except aiosqlite.Error as exc:
        raise DatabaseError("Database operation failed during session") from exc
    finally:
        await db.close()


# ── Query helpers ───────────────────────────────────────────────────────────


async def execute_query(
    db: aiosqlite.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    """Execute a SELECT and return results as a list of plain dicts.

    Never returns raw ``sqlite3.Row`` objects — always materialized dicts
    for JSON serialization safety.

    Args:
        db: Active aiosqlite connection.
        sql: SQL SELECT statement.
        params: Bind parameters.

    Returns:
        List of row dicts. Empty list if no rows match.

    Raises:
        DatabaseError: On any query failure.
    """
    try:
        cursor = await db.execute(sql, params)
        rows = await cursor.fetchall()
        if not rows:
            return []
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except aiosqlite.Error as exc:
        raise DatabaseError(f"Query failed: {sql[:120]}") from exc


async def execute_write(
    db: aiosqlite.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> str:
    """Execute an INSERT/UPDATE/DELETE, commit, and return lastrowid as str.

    Args:
        db: Active aiosqlite connection.
        sql: SQL write statement.
        params: Bind parameters.

    Returns:
        String representation of ``cursor.lastrowid``.

    Raises:
        DatabaseError: On any write or commit failure.
    """
    try:
        cursor = await db.execute(sql, params)
        await db.commit()
        return str(cursor.lastrowid)
    except aiosqlite.Error as exc:
        raise DatabaseError(f"Write failed: {sql[:120]}") from exc
