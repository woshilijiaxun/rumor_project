from flask import Blueprint, request
from application.common.auth import require_auth
from application.common.responses import ok, fail
from application.services import debunks_service

bp = Blueprint('debunks', __name__)


@bp.route('/debunks/live', methods=['GET'])
@require_auth
def get_debunks_live():
    try:
        limit = request.args.get('limit', default=6, type=int)
        url = request.args.get('url') or 'https://www.piyao.org.cn'
        rows = debunks_service.get_today_debunks(limit=limit, url=url)
        return ok(rows)
    except Exception as e:
        return fail(f"抓取失败: {e}", http_code=500, status="error")


@bp.route('/debunks/lianhe', methods=['GET'])
@require_auth
def get_debunks_lianhepiyao():
    try:
        limit = request.args.get('limit', default=6, type=int)
        url = request.args.get('url') or 'https://www.piyao.org.cn'
        rows = debunks_service.get_union_debunks(limit=limit, url=url)
        return ok(rows)
    except Exception as e:
        return fail(f"抓取失败: {e}", http_code=500, status="error")
