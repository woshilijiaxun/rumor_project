from flask import Blueprint, request
from mysql.connector import Error
from application.common.auth import require_auth, require_admin
from application.common.responses import ok, fail
from application.services import algorithms_service

bp = Blueprint('algorithms', __name__)


@bp.route('/algorithms', methods=['GET'])
@require_auth
def list_algorithms():
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        payload = algorithms_service.list_algorithms_paginated(page=page, page_size=page_size)
        return ok(payload)
    except Error as e:
        # 唯一索引冲突：algo_key 重复
        msg = str(e)
        if 'Duplicate entry' in msg and ('ux_algorithms_algo_key' in msg or 'algo_key' in msg):
            return fail("algo_key 已存在，请换一个唯一的 algo_key", http_code=409)
        return fail("数据库错误: " + msg, http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/algorithms', methods=['POST'])
@require_admin
def create_algorithm():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    algo_key = (data.get('algo_key') or '').strip()
    description = (data.get('description') or '').strip()
    algo_type = (data.get('type') or '').strip()
    status = data.get('status', 'active')

    if not name:
        return fail("算法名称不能为空", http_code=400)
    if not algo_key:
        return fail("algo_key 不能为空", http_code=400)

    try:
        algo_id = algorithms_service.create_algorithm(
            name=name,
            algo_key=algo_key,
            description=description,
            algo_type=algo_type,
            status=status,
            actor_meta={
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
            },
        )
        return ok({"id": algo_id}, message="算法创建成功")
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/algorithms/<int:algo_id>', methods=['GET'])
@require_auth
def get_algorithm(algo_id: int):
    try:
        algo = algorithms_service.get_algorithm(algo_id)
        if not algo:
            return fail("算法不存在", http_code=404)
        return ok(algo)
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/algorithms/<int:algo_id>', methods=['PUT'])
@require_admin
def update_algorithm(algo_id: int):
    data = request.get_json() or {}
    name = data.get('name')
    algo_key = data.get('algo_key')
    description = data.get('description')
    algo_type = data.get('type')
    status = data.get('status')

    try:
        if not algorithms_service.get_algorithm(algo_id):
            return fail("算法不存在", http_code=404)
        algorithms_service.update_algorithm(
            algo_id,
            name,
            algo_key,
            description,
            algo_type,
            status,
            actor_meta={
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
            },
        )
        return ok(message="算法已更新")
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/algorithms/<int:algo_id>', methods=['DELETE'])
@require_admin
def delete_algorithm(algo_id: int):
    try:
        if not algorithms_service.get_algorithm(algo_id):
            return fail("算法不存在", http_code=404)
        algorithms_service.delete_algorithm(
            algo_id,
            actor_meta={
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
            },
        )
        return ok(message="算法已删除")
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")
