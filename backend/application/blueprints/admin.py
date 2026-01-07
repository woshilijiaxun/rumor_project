from flask import Blueprint, request, g
from mysql.connector import Error

from application.common.auth import require_auth, require_admin
from application.common.responses import ok, fail
from application.services.system_config_service import get_system_config, update_system_config
from application.services.audit_logs_service import query_logs, write_log

bp = Blueprint('admin', __name__)


@bp.route('/admin/config', methods=['GET'])
@require_auth
@require_admin
def admin_get_config():
    """获取系统配置（管理员）。

    支持：/admin/config?keys=a,b,c
    """
    try:
        keys_param = (request.args.get('keys') or '').strip()
        keys = [k.strip() for k in keys_param.split(',') if k.strip()] if keys_param else None
        cfg = get_system_config(keys)
        return ok(cfg)
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/admin/config', methods=['POST'])
@require_auth
@require_admin
def admin_update_config():
    """更新系统配置（管理员）。

    Body: { "key": "value", ... }
    """
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return fail("配置格式错误：必须是 JSON 对象", http_code=400)

    try:
        uid = None
        try:
            uid = g.user.get('id') if isinstance(getattr(g, 'user', None), dict) else None
        except Exception:
            uid = None

        update_system_config(data, updated_by=uid)

        # 写审计日志（不影响主流程，失败则忽略）
        try:
            write_log(
                actor_user_id=uid,
                action='CONFIG_UPDATE',
                target_type='system_config',
                target_id=None,
                detail={"updated_keys": list(data.keys())},
            )
        except Exception:
            pass

        return ok(message="配置更新成功")
    except ValueError as ve:
        return fail(str(ve), http_code=400)
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/admin/audit-logs', methods=['GET'])
@require_auth
@require_admin
def admin_list_audit_logs():
    """管理员查询审计日志。"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        action = request.args.get('action', None, type=str)
        keyword = request.args.get('keyword', None, type=str)
        payload = query_logs(page=page, page_size=page_size, action=action, keyword=keyword)
        return ok(payload)
    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')
