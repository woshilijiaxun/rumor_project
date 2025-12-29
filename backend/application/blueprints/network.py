import os
from flask import Blueprint, request, current_app
from application.common.auth import require_auth
from application.common.responses import ok, fail
from application.services import uploads_service
from application.services.graph_service import parse_graph_from_file

bp = Blueprint('network', __name__)


@bp.route('/network/graph', methods=['GET'])
@require_auth
def get_network_graph():
    try:
        file_id = request.args.get('file_id', type=int)
        if not file_id:
            return fail('缺少参数: file_id', http_code=400)

        # 可选：限制最大边数，避免超大图压垮前端
        # 不截断：默认不限制；如传入 max_edges 且 >0 则按该值限制
        max_edges = request.args.get('max_edges', type=int)
        if isinstance(max_edges, int):
            if max_edges <= 0:
                max_edges = None
            else:
                max_edges = min(max_edges, 100000)
        else:
            max_edges = None

        row = uploads_service.get_upload_record(file_id)
        if not row:
            return fail('文件不存在', http_code=404)

        stored_name = row['stored_name']
        original_name = row.get('original_name') or stored_name

        # 解析扩展名
        _, ext = os.path.splitext(stored_name or '')
        ext = (ext or '').lstrip('.')
        if not ext:
            _, ext2 = os.path.splitext(original_name or '')
            ext = (ext2 or '').lstrip('.')

        # 构造文件绝对路径
        abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)

        graph = parse_graph_from_file(abs_path=abs_path, ext=ext, max_edges=max_edges)

        return ok({
            'file': {
                'id': row['id'],
                'original_name': row['original_name'],
                'stored_name': row['stored_name'],
                'mime_type': row.get('mime_type', ''),
                'size_bytes': row.get('size_bytes'),
                'storage_path': row.get('storage_path', ''),
            },
            'graph': graph
        })
    except FileNotFoundError:
        return fail('文件不存在', http_code=404)
    except ValueError as e:
        return fail(str(e), http_code=400)
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')

