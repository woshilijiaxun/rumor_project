from __future__ import annotations

import os
import threading
import time
from typing import Optional

from application.repositories import audit_logs_repo


def cleanup_once(days: int = 90) -> int:
    return audit_logs_repo.delete_logs_older_than(days=days)


def start_cleanup_daemon(days: int = 90, interval_hours: int = 24) -> Optional[threading.Thread]:
    """在 Flask 进程内启动一个后台线程定时清理审计日志。

    - 默认每 24 小时跑一次
    - 通过环境变量 AUDIT_CLEANUP_DISABLED=true 可禁用

    注意：多进程部署时每个进程都会启动线程；如你未来用 gunicorn 多 worker，建议改为系统级 cron。
    """
    disabled = (os.getenv('AUDIT_CLEANUP_DISABLED', '') or '').lower() in ('1', 'true', 'yes')
    if disabled:
        return None

    interval_hours = max(int(interval_hours or 24), 1)

    def loop():
        while True:
            try:
                cleanup_once(days=days)
            except Exception:
                pass
            time.sleep(interval_hours * 3600)

    th = threading.Thread(target=loop, name='audit_cleanup_daemon', daemon=True)
    th.start()
    return th

