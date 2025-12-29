from typing import List, Dict, Optional, Tuple
from application.common.db import get_db_connection


def list_users() -> List[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        sql = (
            """
            SELECT 
                id, username, email, created_at,
                UNIX_TIMESTAMP(created_at)*1000 AS created_at_ms
            FROM users 
            ORDER BY id DESC
            """
        )
        cursor.execute(sql)
        return cursor.fetchall() or []
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        return cursor.fetchone()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def username_exists(username: str, exclude_user_id: Optional[int] = None) -> bool:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if exclude_user_id is not None:
            cursor.execute("SELECT 1 FROM users WHERE username=%s AND id<>%s LIMIT 1", (username, exclude_user_id))
        else:
            cursor.execute("SELECT 1 FROM users WHERE username=%s LIMIT 1", (username,))
        return cursor.fetchone() is not None
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def update_user_fields(user_id: int, fields: Dict[str, object]) -> None:
    if not fields:
        return
    columns = []
    params = []
    for k, v in fields.items():
        columns.append(f"{k}=%s")
        params.append(v)
    params.append(user_id)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = f"UPDATE users SET {', '.join(columns)} WHERE id=%s"
        cursor.execute(sql, tuple(params))
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def get_user_public(user_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, created_at FROM users WHERE id=%s", (user_id,))
        return cursor.fetchone()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()

