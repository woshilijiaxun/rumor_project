import os
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from flask import current_app

from application.common.auth import is_admin
from application.services import uploads_service, algorithms_service
from application.repositories import identification_repo
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


def _normalize_list_items(items):
    normalized = []
    for it in items:
        normalized.append({
            'task_id': it.get('task_id'),
            'user_id': it.get('user_id'),
            'file_id': it.get('file_id'),
            'algorithm_key': it.get('algorithm_key'),
            'status': it.get('status'),
            'progress': it.get('progress'),
            'stage': it.get('stage'),
            'message': it.get('message'),
            'created_at': it.get('created_at'),
            'started_at': it.get('started_at'),
            'ended_at': it.get('ended_at'),
            'file_name': it.get('file_name'),
        })
    return normalized


def get_tasks_by_user(user_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 20), 1), 100)
    offset = (page - 1) * page_size

    items, total = identification_repo.list_tasks_by_user(user_id=user_id, offset=offset, limit=page_size)
    total_pages = max((total + page_size - 1) // page_size, 1)

    return {
        'items': _normalize_list_items(items),
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }


def get_tasks(page: int = 1, page_size: int = 20, user_id: Optional[int] = None) -> Dict[str, Any]:
    """管理员用：全量任务列表；也可以按 user_id 过滤。

    注意：应只在 is_admin()==True 的情况下调用。
    """
    if user_id is not None:
        return get_tasks_by_user(user_id=int(user_id), page=page, page_size=page_size)

    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 20), 1), 100)
    offset = (page - 1) * page_size

    items, total = identification_repo.list_all_tasks(offset=offset, limit=page_size)
    total_pages = max((total + page_size - 1) // page_size, 1)

    return {
        'items': _normalize_list_items(items),
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }


def get_task(task_id: str) -> Optional[IdentificationTask]:
    """获取任务：优先从内存取（运行中任务），如无则回退从 DB 取（历史任务）。

    注意：蓝图层会把 IdentificationTask 的 created_at/started_at/ended_at 直接返回给前端。
    内存任务使用 unix time float；DB 任务使用 datetime。这里尽量保持为 datetime（更自然），
    同时不影响前端（前端展示时会 toLocaleString）。
    """
    with _tasks_lock:
        t = _tasks.get(task_id)
    if t:
        return t

    # DB fallback
    try:
        row = identification_repo.get_task_by_id(task_id)
        if not row:
            return None

        # mysql-connector 对 JSON 字段可能返回 str/bytes
        params = row.get('params') or {}
        if isinstance(params, (str, bytes)):
            import json
            params = json.loads(params)

        error = row.get('error')
        if isinstance(error, (str, bytes)):
            import json
            error = json.loads(error)

        task = IdentificationTask(
            task_id=row.get('task_id'),
            user_id=int(row.get('user_id')),
            file_id=int(row.get('file_id')),
            algorithm_key=row.get('algorithm_key') or '',
            params=params or {},
            status=row.get('status') or TASK_STATUS_QUEUED,
            progress=int(row.get('progress') or 0),
            stage=row.get('stage') or '',
            message=row.get('message') or '',
            created_at=0.0,
            started_at=0.0,
            ended_at=0.0,
            result=None,
            error=error,
        )
        # 这里直接把 datetime 透传到对象属性，供蓝图返回
        task.created_at = row.get('created_at')
        task.started_at = row.get('started_at')
        task.ended_at = row.get('ended_at')
        return task
    except Exception:
        return None


def _can_use_upload(current_user_id: int, upload_row: Dict[str, Any]) -> bool:
    """判断当前用户是否允许使用该文件。

    规则：admin 全放开；普通用户仅 public 或 owner。
    """
    if is_admin():
        return True
    if not upload_row:
        return False
    if (upload_row.get('visibility') or 'private') == 'public':
        return True
    try:
        return int(upload_row.get('user_id') or 0) == int(current_user_id)
    except Exception:
        return False


def create_task(app, user_id: int, file_id: int, algorithm_key: str, params: Optional[Dict[str, Any]] = None) -> IdentificationTask:
    """创建异步识别任务（方案2：algo_key）。

    注意：后台线程执行需要 Flask application context，因此必须传入 app 实例。
    """
    # 同步校验：文件权限（public 或 owner；admin 全放开）
    try:
        upload_row = uploads_service.get_upload_record(file_id)
        if not upload_row:
            raise ValueError('文件不存在')
        if not _can_use_upload(user_id, upload_row):
            raise PermissionError('无权限使用该文件')
    except PermissionError:
        # 让上层捕获并返回 403
        raise
    except ValueError:
        raise
    except Exception:
        # 其它异常不阻塞创建（这里选择阻塞更安全）
        raise

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

    # 持久化：写入任务记录（用于历史列表/重启后可查询）
    try:
        identification_repo.create_task_record({
            'task_id': t.task_id,
            'user_id': t.user_id,
            'file_id': t.file_id,
            'algorithm_key': t.algorithm_key,
            'params': t.params,
            'status': t.status,
            'progress': t.progress,
            'stage': t.stage,
            'message': t.message,
            'error': t.error,
            'created_at': t.created_at,
        })
    except Exception:
        # 不影响任务创建与执行
        pass

    th = threading.Thread(target=_run_task, args=(app, t.task_id), daemon=True)
    th.start()
    return t


def delete_task(task_id: str, user_id: int) -> bool:
    try:
        affected = identification_repo.delete_task_by_id(task_id=task_id, user_id=user_id)
        return affected > 0
    except Exception:
        return False


def delete_task_anyway(task_id: str) -> bool:
    try:
        affected = identification_repo.delete_task_anyway(task_id=task_id)
        return affected > 0
    except Exception:
        return False


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


def cancel_task_anyway(task_id: str) -> bool:
    """管理员强制取消运行中任务（仅内存任务）。

    对于已落库的历史任务：取消的语义不明确（可能已经结束），这里保持仅取消内存任务。
    """
    with _tasks_lock:
        t = _tasks.get(task_id)
        if not t:
            return False
        if t.status in (TASK_STATUS_SUCCEEDED, TASK_STATUS_FAILED, TASK_STATUS_CANCELLED):
            return True
        t.status = TASK_STATUS_CANCELLED
        t.stage = 'cancelled'
        t.message = '任务已取消(管理员操作)'
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

    # 持久化：同步到 DB（失败不影响内存任务）
    try:
        identification_repo.update_task_record(task_id, kwargs)
    except Exception:
        pass

    # 若写入成功结果，则 upsert result 表
    if 'result' in kwargs and kwargs.get('result') is not None:
        try:
            identification_repo.upsert_task_result(task_id, kwargs.get('result') or {})
        except Exception:
            pass


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

            # 安全兜底：再次校验文件使用权限（public 或 owner；admin 全放开）
            if not _can_use_upload(task.user_id, row):
                _update_task(task_id, status=TASK_STATUS_FAILED, stage='failed', message='无权限使用该文件', ended_at=_now(), progress=100,
                             error={'code': 'FILE_FORBIDDEN', 'message': '无权限使用该文件'})
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
