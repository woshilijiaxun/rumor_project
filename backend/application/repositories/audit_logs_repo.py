from typing import Any, Dict, List, Optional, Tuple

from application.common.db import get_db_connection


def insert_audit_log(
    actor_user_id: Optional[int],
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO audit_logs(actor_user_id, action, target_type, target_id, detail_json)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                actor_user_id,
                action,
                target_type,
                target_id,
                None if detail is None else __import__('json').dumps(detail, ensure_ascii=False, default=str),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()
        conn.close()


def list_audit_logs(
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
    keyword: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """返回 (items, total). keyword 会匹配 target_id 与 detail_json."""
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 20), 1), 200)
    offset = (page - 1) * page_size

    where = []
    params: List[Any] = []

    if action:
        where.append("action = %s")
        params.append(action)

    if keyword:
        where.append("(target_id LIKE %s OR detail_json LIKE %s)")
        kw = f"%{keyword}%"
        params.extend([kw, kw])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"SELECT COUNT(1) AS c FROM audit_logs {where_sql}", params)
        total = int((cur.fetchone() or {}).get("c") or 0)

        cur.execute(
            f"""
            SELECT id, actor_user_id, action, target_type, target_id, detail_json, created_at
            FROM audit_logs
            {where_sql}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, offset],
        )
        items = cur.fetchall() or []
        return items, total
    finally:
        cur.close()
        conn.close()


def delete_logs_older_than(days: int = 90) -> int:
    """删除超过 days 天的审计日志，返回删除条数。"""
    days = max(int(days or 0), 0)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM audit_logs WHERE created_at < (NOW() - INTERVAL %s DAY)", (days,))
        affected = cur.rowcount or 0
        conn.commit()
        return int(affected)
    finally:
        cur.close()
        conn.close()


def export_audit_logs(
    action: Optional[str] = None,
    keyword: Optional[str] = None,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    limit: int = 50000,
) -> List[Dict[str, Any]]:
    """导出用：按条件返回审计日志列表（最多 limit）。

    start_at/end_at 使用 MySQL 可解析的 datetime 字符串，如：2026-01-01 00:00:00
    """
    limit = min(max(int(limit or 1000), 1), 200000)

    where = []
    params: List[Any] = []

    if action:
        where.append("action = %s")
        params.append(action)

    if keyword:
        where.append("(target_id LIKE %s OR detail_json LIKE %s)")
        kw = f"%{keyword}%"
        params.extend([kw, kw])

    if start_at:
        where.append("created_at >= %s")
        params.append(start_at)

    if end_at:
        where.append("created_at <= %s")
        params.append(end_at)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            f"""
            SELECT id, actor_user_id, action, target_type, target_id, detail_json, created_at
            FROM audit_logs
            {where_sql}
            ORDER BY id DESC
            LIMIT %s
            """,
            params + [limit],
        )
        return cur.fetchall() or []
    finally:
        cur.close()
        conn.close()
