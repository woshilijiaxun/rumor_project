from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error
from application.common.db import get_db_connection
from application.common.auth import create_token
from application.common.responses import ok, fail

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return fail("用户名和密码不能为空", http_code=400)

    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
            if not user:
                return fail("用户名或密码错误", http_code=401)

            stored = user.get('password') or ''
            ok_flag = False
            upgraded = False
            try:
                if check_password_hash(stored, password):
                    ok_flag = True
            except Exception:
                ok_flag = False
            if not ok_flag and stored == password:
                ok_flag = True
                new_hash = generate_password_hash(password)
                ucur = conn.cursor()
                ucur.execute("UPDATE users SET password=%s WHERE id=%s", (new_hash, user['id']))
                conn.commit()
                ucur.close()
                upgraded = True

            if not ok_flag:
                return fail("用户名或密码错误", http_code=401)

            token = create_token(user['id'], user['username'], user.get('role') or 'user')
            from flask import jsonify
            payload = {
                "status": "success",
                "message": "登录成功！" + ("(已自动升级密码存储)" if upgraded else ""),
                "token": token,
                "user": {"id": user['id'], "username": user['username'], "email": user.get('email'), "role": user.get('role') or 'user'},
                "data": {
                    "token": token,
                    "user": {"id": user['id'], "username": user['username'], "email": user.get('email'), "role": user.get('role') or 'user'},
                    "upgraded": upgraded
                }
            }
            return jsonify(payload)
        finally:
            cursor.close()
            conn.close()
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')

    if not username or not password:
        return fail("用户名和密码不能为空", http_code=400)
    if len(username) < 3:
        return fail("用户名至少需要3个字符", http_code=400)
    if len(password) < 6:
        return fail("密码至少需要6个字符", http_code=400)

    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                return fail("用户名已存在", http_code=400)
            pwd_hash = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, pwd_hash, email))
            conn.commit()
            user_id = cursor.lastrowid
            token = create_token(user_id, username, 'user')
            return ok({
                "token": token,
                "user": {"id": user_id, "username": username, "email": email, "role": 'user'}
            }, message="注册成功！")
        finally:
            cursor.close()
            conn.close()
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")

