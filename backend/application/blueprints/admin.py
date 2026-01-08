from flask import Blueprint, request, g, Response
from mysql.connector import Error

from application.common.auth import require_auth, require_admin
from application.common.responses import ok, fail
from application.services.system_config_service import get_system_config, update_system_config
from application.services.audit_logs_service import query_logs
from application.services.audit_logs_export_service import fetch_export_rows, generate_csv_bytes, generate_excel_bytes

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

        update_system_config(
            data,
            updated_by=uid,
            actor_meta={
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
            },
        )

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


@bp.route('/admin/audit-logs/export', methods=['GET'])
@require_auth
@require_admin
def admin_export_audit_logs():
    """管理员导出审计日志（CSV/Excel）。

    Query 参数：
    - type: csv | excel （默认 csv）
    - action, keyword: 同查询接口
    - start_at, end_at: 时间范围（MySQL 可解析的 datetime 字符串）
    - limit: 最大导出条数（默认 50000，最大 200000）

    示例：
    - /api/admin/audit-logs/export?type=csv
    - /api/admin/audit-logs/export?type=excel&start_at=2026-01-01%2000:00:00
    """
    try:
        export_type = (request.args.get('type') or 'csv').strip().lower()
        action = request.args.get('action', None, type=str)
        keyword = request.args.get('keyword', None, type=str)
        start_at = request.args.get('start_at', None, type=str)
        end_at = request.args.get('end_at', None, type=str)
        limit = request.args.get('limit', 50000, type=int)

        rows = fetch_export_rows(
            action=action,
            keyword=keyword,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )

        # 生成文件内容
        if export_type in ('xlsx', 'excel'):
            data = generate_excel_bytes(rows)
            filename = 'audit_logs.xlsx'
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            data = generate_csv_bytes(rows)
            filename = 'audit_logs.csv'
            mimetype = 'text/csv; charset=utf-8'

        return Response(
            data,
            mimetype=mimetype,
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Length': str(len(data)),
            },
        )
    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')
