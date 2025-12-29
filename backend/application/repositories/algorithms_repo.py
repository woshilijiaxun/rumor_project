from typing import List, Dict, Optional
from application.common.db import get_db_connection


def count_algorithms() -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS cnt FROM algorithms")
        row = cursor.fetchone() or {}
        return int(row.get('cnt', 0))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def list_algorithms(offset: int, limit: int) -> List[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, name, algo_key, description, type, status, created_at, updated_at
            FROM algorithms
            ORDER BY id DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset)
        )
        return cursor.fetchall() or []
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def create_algorithm(user_id: Optional[int], name: str, algo_key: str, description: str, algo_type: str, status: str) -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = (
            """
            INSERT INTO algorithms (user_id, name, algo_key, description, type, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
        )
        cursor.execute(sql, (user_id, name, algo_key, description, algo_type, status))
        conn.commit()
        return cursor.lastrowid
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def get_algorithm(algo_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, algo_key, description, type, status, created_at, updated_at FROM algorithms WHERE id=%s",
            (algo_id,)
        )
        return cursor.fetchone()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def get_algorithm_by_key(algo_key: str) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, algo_key, description, type, status, created_at, updated_at FROM algorithms WHERE algo_key=%s",
            (algo_key,)
        )
        return cursor.fetchone()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def update_algorithm_fields(algo_id: int, fields: Dict[str, object]) -> None:
    if not fields:
        return
    columns = []
    params = []
    for k, v in fields.items():
        columns.append(f"{k}=%s")
        params.append(v)
    params.append(algo_id)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = f"UPDATE algorithms SET {', '.join(columns)} WHERE id=%s"
        cursor.execute(sql, tuple(params))
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def delete_algorithm(algo_id: int) -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM algorithms WHERE id=%s", (algo_id,))
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()
