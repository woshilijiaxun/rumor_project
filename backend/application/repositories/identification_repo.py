from typing import Any, Dict, List, Optional, Tuple
import json

from application.common.db import get_db_connection


def create_task_record(task: Dict[str, Any]) -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = (
            """
            INSERT INTO identification_tasks
            (task_id, user_id, file_id, algorithm_key, params, status, progress, stage, message, error, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FROM_UNIXTIME(%s))
            """
        )
        params_json = json.dumps(task.get('params') or {}, ensure_ascii=False)
        error_json = json.dumps(task.get('error'), ensure_ascii=False) if task.get('error') is not None else None
        cursor.execute(
            sql,
            (
                task['task_id'],
                task['user_id'],
                task['file_id'],
                task['algorithm_key'],
                params_json,
                task.get('status') or 'queued',
                int(task.get('progress') or 0),
                task.get('stage') or '',
                task.get('message') or '',
                error_json,
                float(task.get('created_at') or 0.0)
            )
        )
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def update_task_record(task_id: str, fields: Dict[str, Any]) -> None:
    if not fields:
        return

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        sets = []
        vals = []

        mapping = {
            'status': 'status',
            'progress': 'progress',
            'stage': 'stage',
            'message': 'message',
            'error': 'error',
            'started_at': 'started_at',
            'ended_at': 'ended_at'
        }

        for k, col in mapping.items():
            if k not in fields:
                continue
            v = fields.get(k)
            if k in ('started_at', 'ended_at'):
                if v:
                    sets.append(f"{col}=FROM_UNIXTIME(%s)")
                    vals.append(float(v))
                else:
                    sets.append(f"{col}=NULL")
            elif k == 'error':
                sets.append(f"{col}=%s")
                vals.append(json.dumps(v, ensure_ascii=False) if v is not None else None)
            elif k == 'progress':
                sets.append(f"{col}=%s")
                vals.append(int(v or 0))
            else:
                sets.append(f"{col}=%s")
                vals.append(v)

        if not sets:
            return

        sql = f"UPDATE identification_tasks SET {', '.join(sets)} WHERE task_id=%s"
        vals.append(task_id)
        cursor.execute(sql, tuple(vals))
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def upsert_task_result(task_id: str, result: Dict[str, Any]) -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = (
            """
            INSERT INTO identification_task_results (task_id, result)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE result=VALUES(result)
            """
        )
        cursor.execute(sql, (task_id, json.dumps(result or {}, ensure_ascii=False)))
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM identification_tasks WHERE task_id=%s", (task_id,))
        row = cursor.fetchone()
        return row
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def get_task_result(task_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT result FROM identification_task_results WHERE task_id=%s", (task_id,))
        row = cursor.fetchone()
        return row
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def delete_task_by_id(task_id: str, user_id: int) -> int:
    """删除某个用户的任务。

    返回受影响行数（0 表示不存在或无权限）。

    说明：先删 result 表，再删 tasks 表，避免外键约束（若有）。
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # 只删除属于该用户的任务
        cursor.execute(
            "SELECT task_id FROM identification_tasks WHERE task_id=%s AND user_id=%s",
            (task_id, user_id)
        )
        row = cursor.fetchone()
        if not row:
            conn.rollback()
            return 0

        cursor.execute("DELETE FROM identification_task_results WHERE task_id=%s", (task_id,))
        cursor.execute("DELETE FROM identification_tasks WHERE task_id=%s AND user_id=%s", (task_id, user_id))
        affected = cursor.rowcount
        conn.commit()
        return int(affected or 0)
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def delete_task_anyway(task_id: str) -> int:
    """管理员强制删除任务（不校验 user_id）。

    返回受影响行数（0 表示不存在）。
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM identification_task_results WHERE task_id=%s", (task_id,))
        cursor.execute("DELETE FROM identification_tasks WHERE task_id=%s", (task_id,))
        affected = cursor.rowcount
        conn.commit()
        return int(affected or 0)
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def list_tasks_by_user(user_id: int, offset: int, limit: int) -> Tuple[List[Dict[str, Any]], int]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM identification_tasks
            WHERE user_id=%s
            """,
            (user_id,)
        )
        total = int((cursor.fetchone() or {}).get('cnt', 0))

        cursor.execute(
            """
            SELECT
              t.task_id,
              t.user_id,
              t.file_id,
              t.algorithm_key,
              t.status,
              t.progress,
              t.stage,
              t.message,
              t.created_at,
              t.started_at,
              t.ended_at,
              u.original_name AS file_name
            FROM identification_tasks t
            LEFT JOIN uploads u ON u.id = t.file_id
            WHERE t.user_id=%s
            ORDER BY t.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset)
        )
        items = cursor.fetchall() or []
        return items, total
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def list_all_tasks(offset: int, limit: int) -> Tuple[List[Dict[str, Any]], int]:
    """管理员查看全量任务列表。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM identification_tasks
            """
        )
        total = int((cursor.fetchone() or {}).get('cnt', 0))

        cursor.execute(
            """
            SELECT
              t.task_id,
              t.user_id,
              t.file_id,
              t.algorithm_key,
              t.status,
              t.progress,
              t.stage,
              t.message,
              t.created_at,
              t.started_at,
              t.ended_at,
              u.original_name AS file_name
            FROM identification_tasks t
            LEFT JOIN uploads u ON u.id = t.file_id
            ORDER BY t.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset)
        )
        items = cursor.fetchall() or []
        return items, total
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()
