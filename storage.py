import sqlite3
from contextlib import contextmanager


DB_PATH = "alerts.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                chat_id INTEGER NOT NULL,
                area TEXT NOT NULL,
                PRIMARY KEY (chat_id, area)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_alerts (
                alert_id TEXT NOT NULL,
                chat_id INTEGER NOT NULL,
                PRIMARY KEY (alert_id, chat_id)
            )
        """)


def add_subscription(chat_id: int, area: str):
    area = area.strip()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscriptions(chat_id, area) VALUES (?, ?)",
            (chat_id, area)
        )


def remove_subscription(chat_id: int, area: str):
    area = area.strip()
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM subscriptions WHERE chat_id = ? AND area = ?",
            (chat_id, area)
        )


def list_subscriptions(chat_id: int) -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT area FROM subscriptions WHERE chat_id = ? ORDER BY area",
            (chat_id,)
        ).fetchall()
    return [r[0] for r in rows]


def get_all_subscriptions() -> dict[int, set[str]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT chat_id, area FROM subscriptions").fetchall()

    result: dict[int, set[str]] = {}
    for chat_id, area in rows:
        result.setdefault(chat_id, set()).add(area)
    return result


def was_alert_sent(alert_id: str, chat_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM sent_alerts WHERE alert_id = ? AND chat_id = ?",
            (alert_id, chat_id)
        ).fetchone()
    return row is not None


def mark_alert_sent(alert_id: str, chat_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_alerts(alert_id, chat_id) VALUES (?, ?)",
            (alert_id, chat_id)
        )