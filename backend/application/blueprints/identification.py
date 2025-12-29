from flask import Blueprint, request, g, current_app
from mysql.connector import Error

from application.common.auth import require_auth
from application.common.responses import ok, fail
from application.services import identification_service

bp = Blueprint('identification', __name__)


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
        t = identification_service.create_task(
            app=current_app._get_current_object(),
            user_id=g.user['id'],
            file_id=file_id,
            algorithm_key=algorithm_key,
            params=params
        )

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
        if t.user_id != g.user['id']:
            return fail('无权限访问该任务', http_code=403)

        return ok({
            'task_id': t.task_id,
            'file_id': t.file_id,
            'algorithm_key': t.algorithm_key,
            'params': t.params,
            'status': t.status,
            'progress': t.progress,
            'stage': t.stage,
            'message': t.message,
            'created_at': t.created_at,
            'started_at': t.started_at,
            'ended_at': t.ended_at,
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
        if t.user_id != g.user['id']:
            return fail('无权限访问该任务', http_code=403)

        if t.status != identification_service.TASK_STATUS_SUCCEEDED:
            return fail('任务未完成，无法获取结果', http_code=409)

        return ok({
            'task_id': t.task_id,
            'result': t.result or {},
            'meta': {
                'file_id': t.file_id,
                'algorithm_key': t.algorithm_key,
            }
        })

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks/<task_id>/cancel', methods=['POST'])
@require_auth
def cancel_identification_task(task_id: str):
    try:
        ok_cancel = identification_service.cancel_task(task_id=task_id, user_id=g.user['id'])
        if not ok_cancel:
            return fail('任务不存在或无权限', http_code=404)
        return ok(message='任务已取消')

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')
