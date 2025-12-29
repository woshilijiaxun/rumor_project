import traceback
import uuid
import time
from flask import jsonify, g, request


def _json(status: str, message: str, data=None, http_code: int = 500):
    return jsonify({
        "status": status,
        "message": message,
        "data": data,
        "request_id": getattr(g, 'request_id', None)
    }), http_code


class AppError(Exception):
    def __init__(self, message: str, http_code: int = 400, status: str = "fail", data=None):
        super().__init__(message)
        self.message = message
        self.http_code = http_code
        self.status = status
        self.data = data


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return _json(err.status, err.message, err.data, err.http_code)

    @app.errorhandler(400)
    def handle_400(err):
        return _json("fail", "请求无效", http_code=400)

    @app.errorhandler(401)
    def handle_401(err):
        return _json("unauthorized", "未授权", http_code=401)

    @app.errorhandler(404)
    def handle_404(err):
        return _json("fail", "接口不存在", http_code=404)

    @app.errorhandler(Exception)
    def handle_exception(err: Exception):
        # 仅在调试关闭时隐藏栈信息
        app.logger.error("Unhandled error: %s\n%s", err, traceback.format_exc())
        return _json("error", "系统错误" if not app.config.get('DEBUG') else str(err), http_code=500)

