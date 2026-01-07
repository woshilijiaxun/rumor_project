from flask import Blueprint, request, g, current_app
from mysql.connector import Error

from application.common.auth import require_auth, is_admin
from application.common.responses import ok, fail
from application.services import identification_service
from application.services.audit_logs_service import write_log

bp = Blueprint('identification', __name__)


@bp.route('/identification/tasks', methods=['GET'])
@require_auth
def list_identification_tasks():
    try:
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=20, type=int)
        query_user_id = request.args.get('user_id', default=None, type=int)

        if is_admin():
            data = identification_service.get_tasks(page=page, page_size=page_size, user_id=query_user_id)
        else:
            # 普通用户强制只看自己的历史
            data = identification_service.get_tasks_by_user(user_id=g.user['id'], page=page, page_size=page_size)

        return ok(data)
    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks', methods=['POST'])
@require_auth
def create_identification_task():
    try:
        data = request.get_json() or {}
        file_id = data.get('file_id')
        algorithm_key = (data.get('algorithm_key') or data.get('algo_key') or '').strip()
        params = data.get('params') or {}

        if not file_id:
            return fail('缺少参数: file_id', http_code=400)
        if not algorithm_key:
            return fail('缺少参数: algorithm_key', http_code=400)

        try:
            file_id = int(file_id)
        except Exception:
            return fail('参数类型错误: file_id 必须为整数', http_code=400)

        # 传入 app 对象，供后台线程使用 application context
        try:
            t = identification_service.create_task(
                app=current_app._get_current_object(),
                user_id=g.user['id'],
                file_id=file_id,
                algorithm_key=algorithm_key,
                params=params
            )
        except PermissionError:
            return fail('无权限使用该文件', http_code=403)
        except ValueError as ve:
            return fail(str(ve), http_code=400)

        return ok({
            'task_id': t.task_id,
            'status': t.status,
            'progress': t.progress,
            'stage': t.stage,
            'message': t.message,
        }, message='任务创建成功')

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks/<task_id>', methods=['GET'])
@require_auth
def get_identification_task(task_id: str):
    try:
        t = identification_service.get_task(task_id)
        if not t:
            return fail('任务不存在', http_code=404)
        if (not is_admin()) and t.user_id != g.user['id']:
            return fail('无权限访问该任务', http_code=403)

        # created_at/started_at/ended_at 可能是 float(unix time) 或 datetime
        def _ts(v):
            try:
                if hasattr(v, 'isoformat'):
                    return v.isoformat()
                if isinstance(v, (int, float)) and v > 0:
                    import datetime
                    return datetime.datetime.fromtimestamp(v).isoformat()
            except Exception:
                pass
            return None

        return ok({
            'task_id': t.task_id,
            'file_id': t.file_id,
            'algorithm_key': t.algorithm_key,
            'params': t.params,
            'status': t.status,
            'progress': t.progress,
            'stage': t.stage,
            'message': t.message,
            'created_at': _ts(t.created_at),
            'started_at': _ts(t.started_at),
            'ended_at': _ts(t.ended_at),
            'error': t.error,
        })

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks/<task_id>/result', methods=['GET'])
@require_auth
def get_identification_result(task_id: str):
    try:
        t = identification_service.get_task(task_id)
        if not t:
            return fail('任务不存在', http_code=404)
        if (not is_admin()) and t.user_id != g.user['id']:
            return fail('无权限访问该任务', http_code=403)

        if t.status != identification_service.TASK_STATUS_SUCCEEDED:
            return fail('任务未完成，无法获取结果', http_code=409)

        # 结果优先内存，其次 DB
        result = t.result
        if result is None:
            try:
                from application.repositories import identification_repo
                row = identification_repo.get_task_result(t.task_id)
                raw = (row or {}).get('result')
                if isinstance(raw, (str, bytes)):
                    import json
                    result = json.loads(raw)
                elif isinstance(raw, dict):
                    result = raw
            except Exception:
                result = None

        return ok({
            'task_id': t.task_id,
            'result': result or {},
            'meta': {
                'file_id': t.file_id,
                'algorithm_key': t.algorithm_key,
            }
        })

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks/<task_id>', methods=['DELETE'])
@require_auth
def delete_identification_task(task_id: str):
    try:
        if is_admin():
            ok_del = identification_service.delete_task_anyway(task_id=task_id)
        else:
            ok_del = identification_service.delete_task(task_id=task_id, user_id=g.user['id'])

        if not ok_del:
            return fail('任务不存在或无权限', http_code=404)

        # 写审计日志（不影响主流程）
        try:
            write_log(
                actor_user_id=g.user.get('id'),
                action='TASK_DELETE',
                target_type='identification_task',
                target_id=str(task_id),
                detail={'by_admin': bool(is_admin())}
            )
        except Exception:
            pass

        return ok(message='任务已删除')

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks/<task_id>/cancel', methods=['POST'])
@require_auth
def cancel_identification_task(task_id: str):
    try:
        if is_admin():
            ok_cancel = identification_service.cancel_task_anyway(task_id=task_id)
        else:
            ok_cancel = identification_service.cancel_task(task_id=task_id, user_id=g.user['id'])

        if not ok_cancel:
            return fail('任务不存在或无权限', http_code=404)
        return ok(message='任务已取消')

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')
