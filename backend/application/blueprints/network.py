import os
from flask import Blueprint, request, current_app, g
from application.common.auth import require_auth, is_admin
from application.common.responses import ok, fail
from application.services import uploads_service
from application.services.graph_service import parse_graph_from_file
from application.repositories import graph_cache_repo

bp = Blueprint('network', __name__)


@bp.route('/network/graph', methods=['GET'])
@require_auth
def get_network_graph():
    try:
        file_id = request.args.get('file_id', type=int)
        if not file_id:
            return fail('缺少参数: file_id', http_code=400)

        # 可选：限制最大边数，避免超大图压垮前端
        # 默认：历史/详情页希望快速展示，因此默认 max_edges=10000
        max_edges = request.args.get('max_edges', type=int)
        if isinstance(max_edges, int):
            if max_edges <= 0:
                max_edges = 10000
            else:
                max_edges = min(max_edges, 100000)
        else:
            max_edges = 10000

        row = uploads_service.get_upload_record(file_id)
        if not row:
            return fail('文件不存在', http_code=404)

        # 权限：管理员可访问任意；普通用户仅 public 或 owner
        if (not is_admin()) and (row.get('visibility') != 'public') and (int(row.get('user_id') or 0) != int(g.user['id'])):
            return fail('无权限访问该文件', http_code=403)

        force = request.args.get('force', default=0, type=int)

        def _split_first_data_line(line: str):
            # 允许空格/逗号/制表符/分号分隔
            import re
            splitter = re.compile(r"[\s,\t;]+")
            parts = [p for p in splitter.split((line or '').strip()) if p]
            return parts

        # 构造文件绝对路径（先拿到路径用于内容自动检测）
        stored_name = row['stored_name']
        original_name = row.get('original_name') or stored_name

        abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)

        # 自动检测：
        # - 第一行（非空/非注释）只有 2 列 => 单层（source target）
        # - 第一行（非空/非注释）有 4 列 => 多层（layer source target weight）
        # 其他情况默认按单层处理（更保守）
        is_multilayer = False
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                for raw in f:
                    line = (raw or '').strip()
                    if (not line) or line.startswith('#'):
                        continue
                    parts = _split_first_data_line(line)
                    if len(parts) == 4:
                        is_multilayer = True
                    elif len(parts) == 2:
                        is_multilayer = False
                    else:
                        is_multilayer = False
                    break
        except Exception:
            is_multilayer = False

        # 缓存版本需要包含“单层/多层”判定，否则同一文件可能命中错误缓存
        graph_version = 'v2-auto-multilayer' if is_multilayer else 'v2-auto-singlelayer'

        # 文件级缓存（拓扑只由文件决定）
        if not force:
            try:
                cached = graph_cache_repo.get_cached_graph(file_id=file_id, graph_version=graph_version, max_edges=max_edges)
                if cached and cached.get('graph_json'):
                    graph_raw = cached.get('graph_json')
                    import json
                    graph_obj = json.loads(graph_raw) if isinstance(graph_raw, (str, bytes)) else graph_raw

                    return ok({
                        'file': {
                            'id': row['id'],
                            'original_name': row.get('original_name'),
                            'stored_name': row.get('stored_name'),
                            'mime_type': row.get('mime_type', ''),
                            'size_bytes': row.get('size_bytes'),
                            'storage_path': row.get('storage_path', ''),
                            'visibility': row.get('visibility', 'private'),
                            'user_id': row.get('user_id')
                        },
                        'graph': graph_obj,
                        'cache': {
                            'hit': True,
                            'updated_at': str(cached.get('updated_at') or '')
                        }
                    })
            except Exception:
                # 缓存失败不影响主流程
                pass

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

        graph = parse_graph_from_file(
            abs_path=abs_path,
            ext=ext,
            max_edges=max_edges,
            force_multilayer=is_multilayer,
        )

        # 写入缓存（失败不影响返回）
        try:
            meta = graph.get('meta') or {}
            graph_cache_repo.upsert_cached_graph(
                file_id=file_id,
                graph=graph,
                meta=meta,
                graph_version=graph_version,
                max_edges=max_edges
            )
        except Exception:
            pass

        return ok({
            'file': {
                'id': row['id'],
                'original_name': row['original_name'],
                'stored_name': row['stored_name'],
                'mime_type': row.get('mime_type', ''),
                'size_bytes': row.get('size_bytes'),
                'storage_path': row.get('storage_path', ''),
            },
            'graph': graph,
            'cache': {
                'hit': False
            }
        })
    except FileNotFoundError:
        return fail('文件不存在', http_code=404)
    except ValueError as e:
        return fail(str(e), http_code=400)
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')

