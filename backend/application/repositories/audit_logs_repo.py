from typing import Any, Dict, List, Optional, Tuple

from application.common.db import get_conn


def insert_audit_log(
    actor_user_id: Optional[int],
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> int:
    conn = get_conn()
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
                None if detail is None else __import__('json').dumps(detail, ensure_ascii=False),
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

    conn = get_conn()
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

