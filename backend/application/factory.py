import os
import time
import uuid
import logging
from flask import Flask, g, request
from flask_cors import CORS
from config import Config
from .common.errors import register_error_handlers

# 统一初始化与蓝图注册

def create_app() -> Flask:
    app = Flask(__name__)
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

    return app
