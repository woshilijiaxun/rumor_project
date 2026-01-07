from flask import Blueprint, g
from mysql.connector import Error

from application.common.auth import require_auth, require_admin
from application.common.responses import ok, fail
from application.services import stats_service

bp = Blueprint('stats', __name__)


@bp.route('/health', methods=['GET'])
def health():
    return ok({"message": "服务运行正常"})


@bp.route('/stats/me', methods=['GET'])
@require_auth
def stats_me():
    try:
        data = stats_service.get_my_stats(user_id=g.user['id'])
        return ok(data)
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/stats', methods=['GET'])
@require_admin
def stats_overall():
    """全站统计：仅管理员可用（兼容旧路由 /stats）。"""
    try:
        data = stats_service.get_overall_stats()
        return ok(data)
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")
