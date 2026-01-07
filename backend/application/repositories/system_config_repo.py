from typing import Optional, Dict

from application.common.db import get_conn


def get_config(keys: Optional[list[str]] = None) -> Dict[str, str]:
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        if keys:
            placeholders = ','.join(['%s'] * len(keys))
            cur.execute(f"SELECT `key`, `value` FROM system_config WHERE `key` IN ({placeholders})", keys)
        else:
            cur.execute("SELECT `key`, `value` FROM system_config")
        rows = cur.fetchall() or []
        return {r['key']: (r.get('value') if r.get('value') is not None else '') for r in rows}
    finally:
        cur.close()
        conn.close()


def set_config_items(items: Dict[str, str], updated_by: Optional[int] = None) -> None:
    if not items:
        return

    conn = get_conn()
    cur = conn.cursor()
    try:
        for k, v in items.items():
            cur.execute(
                """
                INSERT INTO system_config(`key`, `value`, updated_by)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE `value`=VALUES(`value`), updated_by=VALUES(updated_by)
                """,
                (str(k), None if v is None else str(v), updated_by)
            )
        conn.commit()
    finally:
        cur.close()
        conn.close()

