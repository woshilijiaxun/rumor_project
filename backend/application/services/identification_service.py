import os
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from flask import current_app

from application.services import uploads_service, algorithms_service
from application.algorithms.registry import registry as algo_registry


TASK_STATUS_QUEUED = 'queued'
TASK_STATUS_RUNNING = 'running'
TASK_STATUS_SUCCEEDED = 'succeeded'
TASK_STATUS_FAILED = 'failed'
TASK_STATUS_CANCELLED = 'cancelled'


@dataclass
class IdentificationTask:
    task_id: str
    user_id: int
    file_id: int
    algorithm_key: str
    params: Dict[str, Any]

    status: str = TASK_STATUS_QUEUED
    progress: int = 0
    stage: str = ''
    message: str = ''

    created_at: float = 0.0
    started_at: float = 0.0
    ended_at: float = 0.0

    # result is expected to be a map: {node_id: node_value}
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


_tasks_lock = threading.Lock()
_tasks: Dict[str, IdentificationTask] = {}


def _now() -> float:
    return time.time()


def task_to_public_dict(task: IdentificationTask) -> Dict[str, Any]:
    d = asdict(task)
    if task.status != TASK_STATUS_SUCCEEDED:
        d['result'] = None
    return d


def get_task(task_id: str) -> Optional[IdentificationTask]:
    with _tasks_lock:
        return _tasks.get(task_id)


def create_task(app, user_id: int, file_id: int, algorithm_key: str, params: Optional[Dict[str, Any]] = None) -> IdentificationTask:
    """创建异步识别任务（方案2：algo_key）。

    注意：后台线程执行需要 Flask application context，因此必须传入 app 实例。
    """
    t = IdentificationTask(
        task_id=uuid.uuid4().hex,
        user_id=user_id,
        file_id=file_id,
        algorithm_key=str(algorithm_key or '').strip(),
        params=params or {},
        status=TASK_STATUS_QUEUED,
        progress=0,
        stage='queued',
        message='任务已创建，等待执行',
        created_at=_now(),
    )

    with _tasks_lock:
        _tasks[t.task_id] = t

    th = threading.Thread(target=_run_task, args=(app, t.task_id), daemon=True)
    th.start()
    return t


def cancel_task(task_id: str, user_id: int) -> bool:
    with _tasks_lock:
        t = _tasks.get(task_id)
        if not t:
            return False
        if t.user_id != user_id:
            return False
        if t.status in (TASK_STATUS_SUCCEEDED, TASK_STATUS_FAILED, TASK_STATUS_CANCELLED):
            return True
        t.status = TASK_STATUS_CANCELLED
        t.stage = 'cancelled'
        t.message = '任务已取消'
        t.ended_at = _now()
        return True


def _update_task(task_id: str, **kwargs):
    with _tasks_lock:
        t = _tasks.get(task_id)
        if not t:
            return
        for k, v in kwargs.items():
            if hasattr(t, k):
                setattr(t, k, v)


def _is_cancelled(task_id: str) -> bool:
    with _tasks_lock:
        t = _tasks.get(task_id)
        return bool(t and t.status == TASK_STATUS_CANCELLED)


def _run_task(app, task_id: str):
    """后台线程执行逻辑。必须在 app.app_context() 下运行。"""
    try:
        with app.app_context():
            if _is_cancelled(task_id):
                return

            _update_task(task_id, status=TASK_STATUS_RUNNING, stage='running', message='开始执行', started_at=_now(), progress=1)

            task = get_task(task_id)
            if not task:
                return

            # Validate upload record
            row = uploads_service.get_upload_record(task.file_id)
            if not row:
                _update_task(task_id, status=TASK_STATUS_FAILED, stage='failed', message='文件不存在', ended_at=_now(), progress=100,
                             error={'code': 'FILE_NOT_FOUND', 'message': '文件不存在'})
                return

            # Validate algorithm record by algo_key
            algo_key = (task.algorithm_key or '').strip()
            if not algo_key:
                _update_task(task_id, status=TASK_STATUS_FAILED, stage='failed', message='缺少 algo_key', ended_at=_now(), progress=100,
                             error={'code': 'ALGO_KEY_REQUIRED', 'message': '缺少算法标识 algo_key'})
                return

            algo = algorithms_service.get_algorithm_by_key(algo_key)
            if not algo:
                _update_task(task_id, status=TASK_STATUS_FAILED, stage='failed', message='算法不存在', ended_at=_now(), progress=100,
                             error={'code': 'ALGO_KEY_NOT_FOUND', 'message': f'算法不存在: algo_key={algo_key}'})
                return
            if (algo.get('status') or 'active') != 'active':
                _update_task(task_id, status=TASK_STATUS_FAILED, stage='failed', message='算法未启用', ended_at=_now(), progress=100,
                             error={'code': 'ALGO_INACTIVE', 'message': '算法未启用'})
                return

            stored_name = row.get('stored_name')
            if not stored_name:
                _update_task(task_id, status=TASK_STATUS_FAILED, stage='failed', message='文件记录缺少 stored_name', ended_at=_now(), progress=100,
                             error={'code': 'FILE_RECORD_INVALID', 'message': '文件记录不完整'})
                return

            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            abs_path = os.path.join(upload_folder, stored_name)
            if not os.path.exists(abs_path):
                _update_task(task_id, status=TASK_STATUS_FAILED, stage='failed', message='文件不存在(磁盘)', ended_at=_now(), progress=100,
                             error={'code': 'FILE_MISSING_ON_DISK', 'message': '文件在服务器上不存在'})
                return

            _update_task(task_id, progress=10, stage='loading', message='读取输入数据')
            if _is_cancelled(task_id):
                return

            _update_task(task_id, progress=35, stage='computing', message='执行识别算法')

            spec = algo_registry.get_by_key(algo_key)
            if not spec:
                _update_task(task_id, status=TASK_STATUS_FAILED, stage='failed', message='算法实现未注册', ended_at=_now(), progress=100,
                             error={'code': 'ALGO_IMPL_NOT_FOUND', 'message': f'算法实现未注册: algo_key={algo_key}'})
                return

            def progress_cb(p: int, stage: str = 'computing', msg: str = ''):
                try:
                    p_int = int(p)
                except Exception:
                    p_int = 0
                _update_task(task_id, progress=max(0, min(100, p_int)), stage=stage or 'computing', message=msg or '处理中...')

            def is_cancelled():
                return _is_cancelled(task_id)

            result = spec.runner(abs_path, task.params or {}, progress_cb, is_cancelled)

            if _is_cancelled(task_id):
                return

            _update_task(task_id, progress=90, stage='finalizing', message='整理结果')
            if _is_cancelled(task_id):
                return

            result_str_keys = {str(k): v for k, v in (result or {}).items()}
            _update_task(task_id, status=TASK_STATUS_SUCCEEDED, progress=100, stage='succeeded', message='识别完成', ended_at=_now(), result=result_str_keys, error=None)

    except Exception as e:
        _update_task(task_id, status=TASK_STATUS_FAILED, progress=100, stage='failed', message='系统错误', ended_at=_now(),
                     error={'code': 'INTERNAL_ERROR', 'message': str(e)})
