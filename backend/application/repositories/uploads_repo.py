from typing import List, Dict, Optional
from application.common.db import get_db_connection


def create_upload(user_id: int, original_name: str, stored_name: str, mime_type: str, size_bytes: int, storage_path: str, visibility: str = 'private') -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = (
            """
            INSERT INTO uploads (user_id, visibility, original_name, stored_name, mime_type, size_bytes, storage_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
        )
        cursor.execute(sql, (user_id, (visibility or 'private'), original_name, stored_name, mime_type, size_bytes, storage_path))
        conn.commit()
        return cursor.lastrowid
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def count_uploads(where_sql: str = "", params: tuple = ()) -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT COUNT(*) AS cnt FROM uploads"
        if where_sql:
            sql += " WHERE " + where_sql
        cursor.execute(sql, params)
        row = cursor.fetchone() or {}
        return int(row.get('cnt', 0))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def list_uploads(offset: int, limit: int, where_sql: str = "", params: tuple = ()) -> List[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        base_sql = (
            """
            SELECT id, user_id, visibility, original_name, stored_name, mime_type, size_bytes, storage_path, created_at
            FROM uploads
            """
        )
        if where_sql:
            base_sql += " WHERE " + where_sql + "\n"
        base_sql += " ORDER BY id DESC\n LIMIT %s OFFSET %s"
        cursor.execute(base_sql, tuple(params) + (limit, offset))
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

