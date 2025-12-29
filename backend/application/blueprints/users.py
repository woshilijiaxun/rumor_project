from flask import Blueprint, request, g
from mysql.connector import Error
from application.common.auth import require_auth
from application.common.responses import ok, fail
from application.services import users_service

bp = Blueprint('users', __name__)


@bp.route('/users', methods=['GET'])
@require_auth
def get_users():
    try:
        users = users_service.list_users()
        return ok(users)
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/users/update', methods=['POST'])
@require_auth
def update_user():
    data = request.get_json() or {}
    user_id = g.user['id']
    new_username = data.get('username')
    new_email = data.get('email')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    try:
        updated = users_service.update_user(
            user_id=user_id,
            new_username=new_username,
            new_email=new_email,
            old_password=old_password,
            new_password=new_password
        )
        return ok(updated, message="资料已更新")
    except ValueError as ve:
        return fail(str(ve), http_code=400)
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")
