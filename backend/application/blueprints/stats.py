from flask import Blueprint
from mysql.connector import Error
from application.common.db import get_db_connection
from application.common.auth import require_auth
from application.common.responses import ok, fail

bp = Blueprint('stats', __name__)

@bp.route('/health', methods=['GET'])
def health():
    return ok({"message": "服务运行正常"})

@bp.route('/stats', methods=['GET'])
@require_auth
def stats():
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) AS users_total, MAX(created_at) AS latest_user_created_at FROM users")
            row = cursor.fetchone() or {}
            return ok({
                "users_total": row.get('users_total', 0),
                "latest_user_created_at": row.get('latest_user_created_at')
            })
        finally:
            cursor.close()
            conn.close()
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")

