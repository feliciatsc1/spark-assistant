"""
database.py — SQLite storage for goals and journal entries
"""
import sqlite3
import os
from datetime import datetime
from zoneinfo import ZoneInfo

DB_PATH  = os.environ.get("DB_PATH", "assistant.db")
TIMEZONE = "Asia/Kuala_Lumpur"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS goals (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                title          TEXT    NOT NULL,
                progress_notes TEXT    DEFAULT '',
                completed      INTEGER DEFAULT 0,
                created_at     TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS journal (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                entry      TEXT    NOT NULL,
                created_at TEXT    NOT NULL
            );
        """)


def now_myt() -> str:
    return datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d %H:%M")


# ── Goals ─────────────────────────────────────────────────────────────────────

def add_goal(user_id: int, title: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO goals (user_id, title, created_at) VALUES (?, ?, ?)",
            (user_id, title, now_myt()),
        )
        return cur.lastrowid


def list_goals(user_id: int) -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM goals WHERE user_id=? AND completed=0 ORDER BY id",
            (user_id,),
        ).fetchall()


def all_goals(user_id: int) -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM goals WHERE user_id=? ORDER BY completed, id",
            (user_id,),
        ).fetchall()


def add_goal_note(user_id: int, goal_id: int, note: str) -> bool:
    with get_conn() as conn:
        goal = conn.execute(
            "SELECT * FROM goals WHERE id=? AND user_id=?",
            (goal_id, user_id),
        ).fetchone()
        if not goal:
            return False
        existing = goal["progress_notes"] or ""
        updated  = f"{existing}\n• [{now_myt()}] {note}".strip()
        conn.execute("UPDATE goals SET progress_notes=? WHERE id=?", (updated, goal_id))
        return True


def complete_goal(user_id: int, goal_id: int) -> bool:
    with get_conn() as conn:
        result = conn.execute(
            "UPDATE goals SET completed=1 WHERE id=? AND user_id=?",
            (goal_id, user_id),
        )
        return result.rowcount > 0


def delete_goal(user_id: int, goal_id: int) -> bool:
    with get_conn() as conn:
        result = conn.execute(
            "DELETE FROM goals WHERE id=? AND user_id=?",
            (goal_id, user_id),
        )
        return result.rowcount > 0


# ── Journal ───────────────────────────────────────────────────────────────────

def add_journal(user_id: int, entry: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO journal (user_id, entry, created_at) VALUES (?, ?, ?)",
            (user_id, entry, now_myt()),
        )
        return cur.lastrowid


def list_journal(user_id: int, limit: int = 5) -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM journal WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()


def search_journal(user_id: int, keyword: str) -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM journal WHERE user_id=? AND entry LIKE ? ORDER BY id DESC LIMIT 10",
            (user_id, f"%{keyword}%"),
        ).fetchall()


def recent_journal_text(user_id: int, limit: int = 10) -> str:
    entries = list_journal(user_id, limit)
    if not entries:
        return "No journal entries yet."
    return "\n\n".join(
        [f"[{e['created_at']}]\n{e['entry']}" for e in reversed(entries)]
    )
