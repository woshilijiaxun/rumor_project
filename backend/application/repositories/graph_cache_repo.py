from typing import Any, Dict, Optional
import json

from application.common.db import get_db_connection


def get_cached_graph(file_id: int, graph_version: str, max_edges: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT file_id, graph_json, meta_json, graph_version, max_edges, updated_at
            FROM file_graph_cache
            WHERE file_id=%s AND graph_version=%s AND max_edges=%s
            """,
            (file_id, graph_version, max_edges)
        )
        row = cursor.fetchone()
        return row
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def upsert_cached_graph(file_id: int, graph: Dict[str, Any], meta: Dict[str, Any], graph_version: str, max_edges: int) -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = (
            """
            INSERT INTO file_graph_cache (file_id, graph_json, meta_json, graph_version, max_edges)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                graph_json=VALUES(graph_json),
                meta_json=VALUES(meta_json),
                graph_version=VALUES(graph_version),
                max_edges=VALUES(max_edges)
            """
        )
        cursor.execute(
            sql,
            (
                file_id,
                json.dumps(graph or {}, ensure_ascii=False),
                json.dumps(meta or {}, ensure_ascii=False),
                graph_version,
                int(max_edges)
            )
        )
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()

