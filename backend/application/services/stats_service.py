from typing import Dict, Any
from application.common.db import get_db_connection


def get_my_stats(user_id: int) -> Dict[str, Any]:
    """普通用户可用：我的统计。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # 我的上传数
        cursor.execute("SELECT COUNT(*) AS cnt FROM uploads WHERE user_id=%s", (user_id,))
        uploads_total = int((cursor.fetchone() or {}).get('cnt', 0))

        # 我的任务数/成功/失败，以及最近一次任务时间
        cursor.execute(
            """
            SELECT
              COUNT(*) AS tasks_total,
              SUM(CASE WHEN status='succeeded' THEN 1 ELSE 0 END) AS tasks_succeeded,
              SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS tasks_failed,
              MAX(created_at) AS latest_task_created_at
            FROM identification_tasks
            WHERE user_id=%s
            """,
            (user_id,)
        )
        row = cursor.fetchone() or {}

        return {
            'uploads_total': uploads_total,
            'tasks_total': int(row.get('tasks_total') or 0),
            'tasks_succeeded': int(row.get('tasks_succeeded') or 0),
            'tasks_failed': int(row.get('tasks_failed') or 0),
            'latest_task_created_at': row.get('latest_task_created_at'),
        }
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


def get_overall_stats() -> Dict[str, Any]:
    """管理员可用：全站统计。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS users_total, MAX(created_at) AS latest_user_created_at FROM users")
        users_row = cursor.fetchone() or {}

        cursor.execute("SELECT COUNT(*) AS uploads_total FROM uploads")
        uploads_row = cursor.fetchone() or {}

        cursor.execute(
            """
            SELECT
              COUNT(*) AS tasks_total,
              SUM(CASE WHEN status='succeeded' THEN 1 ELSE 0 END) AS tasks_succeeded,
              SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS tasks_failed,
              MAX(created_at) AS latest_task_created_at
            FROM identification_tasks
            """
        )
        tasks_row = cursor.fetchone() or {}

        return {
            'users_total': int(users_row.get('users_total') or 0),
            'latest_user_created_at': users_row.get('latest_user_created_at'),
            'uploads_total': int(uploads_row.get('uploads_total') or 0),
            'tasks_total': int(tasks_row.get('tasks_total') or 0),
            'tasks_succeeded': int(tasks_row.get('tasks_succeeded') or 0),
            'tasks_failed': int(tasks_row.get('tasks_failed') or 0),
            'latest_task_created_at': tasks_row.get('latest_task_created_at'),
        }
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()

