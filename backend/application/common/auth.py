import datetime as dt
from functools import wraps
from flask import request, jsonify, g
import jwt
from config import Config

# JWT 配置
JWT_ALG = 'HS256'
JWT_EXPIRE_SECONDS = 24 * 60 * 60  # 24小时


def create_token(user_id: int, username: str) -> str:
    payload = {
        'sub': user_id,
        'username': username,
        'iat': int(dt.datetime.utcnow().timestamp()),
        'exp': int((dt.datetime.utcnow() + dt.timedelta(seconds=JWT_EXPIRE_SECONDS)).timestamp())
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm=JWT_ALG)


def decode_token(token: str):
    # 增加 60 秒容忍时钟偏差
    return jwt.decode(token, Config.SECRET_KEY, algorithms=[JWT_ALG], leeway=60)


def get_token_from_request():
    # 优先从 Authorization: Bearer <token>
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth.split(' ', 1)[1].strip()
    # 兼容下载/预览链接中的 ?token=
    token = request.args.get('token')
    if token:
        return token
    return None


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({'status': 'unauthorized', 'message': '未提供令牌'}), 401
        try:
            payload = decode_token(token)
            g.user = {'id': int(payload.get('sub')), 'username': payload.get('username')}
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'unauthorized', 'message': '令牌已过期'}), 401
        except Exception:
            return jsonify({'status': 'unauthorized', 'message': '令牌无效'}), 401
        return f(*args, **kwargs)
    return wrapper

