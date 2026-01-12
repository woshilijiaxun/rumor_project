from flask import Blueprint, request, g, current_app
from mysql.connector import Error
import os
import networkx as nx

from application.common.auth import require_auth, is_admin
from application.common.responses import ok, fail
from application.services import identification_service, uploads_service
from application.services.graph_service import parse_graph_from_file
from application.services.propagation_service import PropagationSimulator, threshhold

bp = Blueprint('identification', __name__)


@bp.route('/identification/tasks', methods=['GET'])
@require_auth
def list_identification_tasks():
    try:
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=20, type=int)
        query_user_id = request.args.get('user_id', default=None, type=int)

        if is_admin():
            data = identification_service.get_tasks(page=page, page_size=page_size, user_id=query_user_id)
        else:
            # 普通用户强制只看自己的历史
            data = identification_service.get_tasks_by_user(user_id=g.user['id'], page=page, page_size=page_size)

        return ok(data)
    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks', methods=['POST'])
@require_auth
def create_identification_task():
    try:
        data = request.get_json() or {}
        file_id = data.get('file_id')
        algorithm_key = (data.get('algorithm_key') or data.get('algo_key') or '').strip()
        params = data.get('params') or {}

        if not file_id:
            return fail('缺少参数: file_id', http_code=400)
        if not algorithm_key:
            return fail('缺少参数: algorithm_key', http_code=400)

        try:
            file_id = int(file_id)
        except Exception:
            return fail('参数类型错误: file_id 必须为整数', http_code=400)

        # 传入 app 对象，供后台线程使用 application context
        try:
            t = identification_service.create_task(
                app=current_app._get_current_object(),
                user_id=g.user['id'],
                file_id=file_id,
                algorithm_key=algorithm_key,
                params=params,
                actor_meta={
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                },
            )
        except PermissionError:
            return fail('无权限使用该文件', http_code=403)
        except ValueError as ve:
            return fail(str(ve), http_code=400)

        return ok({
            'task_id': t.task_id,
            'status': t.status,
            'progress': t.progress,
            'stage': t.stage,
            'message': t.message,
        }, message='任务创建成功')

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks/<task_id>', methods=['GET'])
@require_auth
def get_identification_task(task_id: str):
    try:
        t = identification_service.get_task(task_id)
        if not t:
            return fail('任务不存在', http_code=404)
        if (not is_admin()) and t.user_id != g.user['id']:
            return fail('无权限访问该任务', http_code=403)

        # created_at/started_at/ended_at 可能是 float(unix time) 或 datetime
        def _ts(v):
            try:
                if hasattr(v, 'isoformat'):
                    return v.isoformat()
                if isinstance(v, (int, float)) and v > 0:
                    import datetime
                    return datetime.datetime.fromtimestamp(v).isoformat()
            except Exception:
                pass
            return None

        return ok({
            'task_id': t.task_id,
            'file_id': t.file_id,
            'algorithm_key': t.algorithm_key,
            'params': t.params,
            'status': t.status,
            'progress': t.progress,
            'stage': t.stage,
            'message': t.message,
            'created_at': _ts(t.created_at),
            'started_at': _ts(t.started_at),
            'ended_at': _ts(t.ended_at),
            'error': t.error,
        })

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks/<task_id>/result', methods=['GET'])
@require_auth
def get_identification_result(task_id: str):
    try:
        t = identification_service.get_task(task_id)
        if not t:
            return fail('任务不存在', http_code=404)
        if (not is_admin()) and t.user_id != g.user['id']:
            return fail('无权限访问该任务', http_code=403)

        if t.status != identification_service.TASK_STATUS_SUCCEEDED:
            return fail('任务未完成，无法获取结果', http_code=409)

        # 结果优先内存，其次 DB
        result = t.result
        if result is None:
            try:
                from application.repositories import identification_repo
                row = identification_repo.get_task_result(t.task_id)
                raw = (row or {}).get('result')
                if isinstance(raw, (str, bytes)):
                    import json
                    result = json.loads(raw)
                elif isinstance(raw, dict):
                    result = raw
            except Exception:
                result = None

        return ok({
            'task_id': t.task_id,
            'result': result or {},
            'meta': {
                'file_id': t.file_id,
                'algorithm_key': t.algorithm_key,
            }
        })

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks/<task_id>', methods=['DELETE'])
@require_auth
def delete_identification_task(task_id: str):
    try:
        if is_admin():
            ok_del = identification_service.delete_task_anyway(
                task_id=task_id,
                actor_user_id=g.user.get('id'),
                actor_meta={
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                },
            )
        else:
            ok_del = identification_service.delete_task(
                task_id=task_id,
                user_id=g.user['id'],
                actor_meta={
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                },
            )

        if not ok_del:
            return fail('任务不存在或无权限', http_code=404)


        return ok(message='任务已删除')

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/tasks/<task_id>/cancel', methods=['POST'])
@require_auth
def cancel_identification_task(task_id: str):
    try:
        if is_admin():
            ok_cancel = identification_service.cancel_task_anyway(
                task_id=task_id,
                actor_user_id=g.user.get('id'),
                actor_meta={
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                },
            )
        else:
            ok_cancel = identification_service.cancel_task(
                task_id=task_id,
                user_id=g.user['id'],
                actor_meta={
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                },
            )

        if not ok_cancel:
            return fail('任务不存在或无权限', http_code=404)
        return ok(message='任务已取消')

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')


@bp.route('/identification/propagation', methods=['POST'])
@require_auth
def identification_propagation():
    """基于识别结果(top-k) + SIR 仿真，输出概率传播图。

    前端建议请求体：
    {
      "task_id": "...",        # 必填：识别任务 id（必须已完成）
      "mode": "single",       # 可选：single(逐个种子) / multi(联合种子)
      "k": 10,                 # 可选：取识别结果前 k 个
      "beta": 0.12,            # 可选：不传则自动按阈值计算
      "num_simulations": 500   # 可选：蒙特卡洛次数
    }

    返回：
      - single: 每个种子对应一个 probability_graph
      - multi: 整体一个 probability_graph
    """
    try:
        data = request.get_json() or {}
        task_id = (data.get('task_id') or '').strip()
        mode = (data.get('mode') or 'single').strip().lower()
        k = data.get('k', 10)
        beta = data.get('beta', None)
        num_simulations = data.get('num_simulations', 10)

        if not task_id:
            return fail('缺少参数: task_id', http_code=400)
        if mode not in ('single', 'multi'):
            return fail('参数错误: mode 必须为 single 或 multi', http_code=400)

        try:
            k = int(k)
        except Exception:
            return fail('参数类型错误: k 必须为整数', http_code=400)
        if k <= 0:
            return fail('参数错误: k 必须 > 0', http_code=400)

        try:
            num_simulations = int(num_simulations)
        except Exception:
            return fail('参数类型错误: num_simulations 必须为整数', http_code=400)
        if num_simulations <= 0:
            return fail('参数错误: num_simulations 必须 > 0', http_code=400)

        if beta is not None:
            try:
                beta = float(beta)
            except Exception:
                return fail('参数类型错误: beta 必须为数字', http_code=400)
            if beta <= 0:
                return fail('参数错误: beta 必须 > 0', http_code=400)

        # 读取任务并校验权限
        t = identification_service.get_task(task_id)
        if not t:
            return fail('任务不存在', http_code=404)
        if (not is_admin()) and t.user_id != g.user['id']:
            return fail('无权限访问该任务', http_code=403)
        if t.status != identification_service.TASK_STATUS_SUCCEEDED:
            return fail('任务未完成，无法进行传播仿真', http_code=409)

        # 获取识别结果（优先内存，其次 DB）
        result = t.result
        if result is None:
            try:
                from application.repositories import identification_repo
                row = identification_repo.get_task_result(t.task_id)
                raw = (row or {}).get('result')
                if isinstance(raw, (str, bytes)):
                    import json
                    result = json.loads(raw)
                elif isinstance(raw, dict):
                    result = raw
            except Exception:
                result = None
        result = result or {}

        # 从结果里取 top-k：按 value(影响力/分数)降序
        try:
            sorted_items = sorted(result.items(), key=lambda kv: float(kv[1]), reverse=True)
        except Exception:
            # 兜底：无法转 float 时按字符串
            sorted_items = sorted(result.items(), key=lambda kv: str(kv[1]), reverse=True)

        topk_nodes = [str(kv[0]) for kv in sorted_items[:k]]
        if not topk_nodes:
            return fail('识别结果为空，无法进行传播仿真', http_code=409)

        # 加载图（复用上传文件）
        row = uploads_service.get_upload_record(int(t.file_id))
        if not row:
            return fail('文件不存在', http_code=404)

        stored_name = row.get('stored_name')
        original_name = row.get('original_name') or stored_name
        if not stored_name:
            return fail('文件记录不完整: stored_name', http_code=500, status='error')

        _, ext = os.path.splitext(stored_name or '')
        ext = (ext or '').lstrip('.')
        if not ext:
            _, ext2 = os.path.splitext(original_name or '')
            ext = (ext2 or '').lstrip('.')

        abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
        graph_obj = parse_graph_from_file(abs_path=abs_path, ext=ext, max_edges=None)

        # 构建 networkx 无向图
        G = nx.Graph()
        for n in graph_obj.get('nodes') or []:
            nid = str((n or {}).get('id'))
            if nid:
                G.add_node(nid)
        for e in graph_obj.get('edges') or []:
            s = str((e or {}).get('source'))
            tt = str((e or {}).get('target'))
            if s and tt:
                G.add_edge(s, tt)

        if beta is None:
            beta = threshhold(G)

        simulator = PropagationSimulator(G)

        if mode == 'single':
            graphs = {}
            for seed in topk_nodes:
                graphs[seed] = simulator.calculate_propagation(
                    beta=beta,
                    source_nodes=[seed],
                    num_simulations=num_simulations,
                )
            return ok({
                'mode': 'single',
                'task_id': task_id,
                'file_id': t.file_id,
                'k': k,
                'beta': beta,
                'num_simulations': num_simulations,
                'topk_nodes': topk_nodes,
                'probability_graphs': graphs,
            })

        # mode == 'multi'
        prob_graph = simulator.calculate_propagation(
            beta=beta,
            source_nodes=topk_nodes,
            num_simulations=num_simulations,
        )
        return ok({
            'mode': 'multi',
            'task_id': task_id,
            'file_id': t.file_id,
            'k': k,
            'beta': beta,
            'num_simulations': num_simulations,
            'source_nodes': topk_nodes,
            'probability_graph': prob_graph,
        })

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')
