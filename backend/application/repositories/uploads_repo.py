from typing import List, Dict, Optional, Tuple
from application.common.db import get_db_connection


def create_upload(user_id: int, original_name: str, stored_name: str, mime_type: str, size_bytes: int, storage_path: str) -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = (
            """
            INSERT INTO uploads (user_id, original_name, stored_name, mime_type, size_bytes, storage_path)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
        )
        cursor.execute(sql, (user_id, original_name, stored_name, mime_type, size_bytes, storage_path))
        conn.commit()
        return cursor.lastrowid
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def count_uploads() -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS cnt FROM uploads")
        row = cursor.fetchone() or {}
        return int(row.get('cnt', 0))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def list_uploads(offset: int, limit: int) -> List[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, user_id, original_name, stored_name, mime_type, size_bytes, storage_path, created_at
            FROM uploads
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


def get_upload_by_id(file_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM uploads WHERE id=%s", (file_id,))
        return cursor.fetchone()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def delete_upload(file_id: int) -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM uploads WHERE id=%s", (file_id,))
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()

