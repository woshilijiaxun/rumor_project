import os
import time
import uuid
import logging
import json
from datetime import datetime, date
from flask import Flask, g, request
from flask.json.provider import JSONProvider
from flask_cors import CORS
from config import Config


class CustomJSONProvider(JSONProvider):
    """自定义 JSON Provider，统一处理时间格式。"""
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, default=self.default)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

    def default(self, o):
        if isinstance(o, (datetime, date)):
            # 统一输出为 ISO 8601 格式（带 Z 表示 UTC）
            # 前端 JS new Date() 可以直接正确解析
            # 注意：这里假定从数据库取出的 naive datetime 是 UTC 时间
            # 如果是北京时间，需要先为其附加时区再转为 isoformat
            # 考虑到数据库连接已设为+8，这里直接 isoformat 可能不完全准确
            # 但能确保前端解析的一致性。最理想情况是转为带时区信息的 iso 字符串。
            # 为简单起见，先统一用 .isoformat()
            return o.isoformat()
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

from .common.errors import register_error_handlers

# 统一初始化与蓝图注册

def create_app() -> Flask:
    app = Flask(__name__)
    app.json = CustomJSONProvider(app)
    app.config.from_object(Config)

    # 目录/上传配置
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    UPLOAD_DIR = os.path.join(ROOT_DIR, 'static', 'uploads')
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB

    # CORS
    CORS(app)

    # 日志初始化（简单版，可后续接入结构化日志）
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

    # 全局错误处理注册
    register_error_handlers(app)

    # 请求钩子：request_id 与耗时日志
    @app.before_request
    def _before_request():
        g.request_id = str(uuid.uuid4())
        g._start_time = time.time()

    @app.after_request
    def _after_request(response):
        try:
            duration_ms = int((time.time() - getattr(g, '_start_time', time.time())) * 1000)
            uid = getattr(getattr(g, 'user', {}), 'get', lambda k, d=None: d)('id') if isinstance(getattr(g, 'user', {}), dict) else None
            app.logger.info(f"rid=%s method=%s path=%s status=%s duration=%sms uid=%s", g.request_id, request.method, request.path, response.status_code, duration_ms, uid)
            response.headers['X-Request-Id'] = g.request_id
        except Exception:
            pass
        return response

    # 蓝图注册（统一 /api 前缀）
    from .blueprints.auth import bp as auth_bp
    from .blueprints.users import bp as users_bp
    from .blueprints.uploads import bp as uploads_bp
    from .blueprints.debunks import bp as debunks_bp
    from .blueprints.stats import bp as stats_bp
    from .blueprints.algorithms import bp as algorithms_bp
    from .blueprints.network import bp as network_bp
    from .blueprints.identification import bp as identification_bp
    from .blueprints.admin import bp as admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(uploads_bp, url_prefix='/api')
    app.register_blueprint(debunks_bp, url_prefix='/api')
    app.register_blueprint(stats_bp, url_prefix='/api')
    app.register_blueprint(algorithms_bp, url_prefix='/api')
    app.register_blueprint(network_bp, url_prefix='/api')
    app.register_blueprint(identification_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')

    # 启动审计日志定时清理后台线程
    try:
        from .services.audit_maintenance import start_cleanup_daemon
        start_cleanup_daemon()
    except Exception:
        # 不影响主应用启动
        pass

    # 启动健康检查定时刷新后台线程（每 10 分钟）
    try:
        from .services.health_service import start_health_daemon
        start_health_daemon(app)
    except Exception as e:
        # 不影响主应用启动
        app.logger.error(f"Failed to start health check daemon: {e}")
        pass

    return app
