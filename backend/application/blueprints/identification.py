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


def _safe_float(v, default=None):
    try:
        return float(v)
    except Exception:
        return default


def _safe_int(v, default=None):
    try:
        return int(v)
    except Exception:
        return default


def _compute_graph_metrics(G: nx.Graph, graph_obj: dict, top_nodes: list[str]) -> dict:
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()

    # --- 基础结构指标（全图口径） ---
    # 密度（无向简单图近似）：2E/(N(N-1))
    density = (2.0 * num_edges / (num_nodes * (num_nodes - 1))) if num_nodes and num_nodes > 1 else 0.0

    # 平均度（无向图）：2E/N
    avg_degree = (2.0 * num_edges / num_nodes) if num_nodes else 0.0

    # --- 高阶指标（最大连通分量口径） ---
    lcc_avg_path_length = None
    lcc_avg_clustering = None
    lcc_transitivity = None
    lcc_nodes = None
    lcc_edges = None
    num_components = 0
    largest_component_ratio = 0.0

    try:
        if num_nodes > 0:
            connected_components = list(nx.connected_components(G))
            num_components = len(connected_components)

            # 最大连通分量
            largest_cc = max(connected_components, key=len)
            largest_component_ratio = len(largest_cc) / num_nodes
            H = G.subgraph(largest_cc).copy()
            lcc_nodes = H.number_of_nodes()
            lcc_edges = H.number_of_edges()

            # 平均最短路径长度（在最大连通分量上才有定义）
            if H.number_of_nodes() > 1:
                lcc_avg_path_length = nx.average_shortest_path_length(H)
            else:
                lcc_avg_path_length = 0.0

            # 平均聚类系数 / 全局聚类系数
            lcc_avg_clustering = nx.average_clustering(H)
            lcc_transitivity = nx.transitivity(H)
    except Exception:
        # 任何异常都不影响报告主流程
        pass

    # Top 节点度
    top_node_metrics = {}
    for nid in top_nodes:
        if G.has_node(nid):
            deg = G.degree(nid)
            neighbors = list(G.neighbors(nid))
        else:
            deg = 0
            neighbors = []
        top_node_metrics[str(nid)] = {
            'degree': deg,
            'neighbors_sample': sorted(neighbors)[:10]
        }

    return {
        'graph_summary': {
            'nodes': num_nodes,
            'edges': num_edges,
            'density': density,
            'avg_degree': avg_degree,
            'components': num_components,
            'largest_component_ratio': largest_component_ratio,
            'truncated': bool((graph_obj.get('meta') or {}).get('truncated')),
            'max_edges': (graph_obj.get('meta') or {}).get('max_edges'),
        },
        'largest_component_metrics': {
            'basis': 'largest_connected_component',
            'nodes': lcc_nodes,
            'edges': lcc_edges,
            'avg_path_length': lcc_avg_path_length,
            'avg_clustering': lcc_avg_clustering,
            'transitivity': lcc_transitivity,
        },
        'top_node_metrics': top_node_metrics,
    }


def _score_distribution(scores: list[float]) -> dict:
    scores = [s for s in scores if isinstance(s, (int, float))]
    if not scores:
        return {
            'count': 0,
            'min': None,
            'max': None,
            'mean': None,
            'median': None,
        }
    scores_sorted = sorted(scores)
    n = len(scores_sorted)
    mn = scores_sorted[0]
    mx = scores_sorted[-1]
    mean = sum(scores_sorted) / n
    if n % 2 == 1:
        med = scores_sorted[n // 2]
    else:
        med = (scores_sorted[n // 2 - 1] + scores_sorted[n // 2]) / 2.0
    return {
        'count': n,
        'min': mn,
        'max': mx,
        'mean': mean,
        'median': med,
    }


def _risk_level(top_scores: list[float], all_scores: list[float]) -> dict:
    # 规则化、可解释：头部集中 + top1 突出
    dist = _score_distribution(all_scores)
    if not all_scores:
        return {'level': 'unknown', 'reason': '结果为空'}

    scores_sorted = sorted([s for s in all_scores if isinstance(s, (int, float))], reverse=True)
    if not scores_sorted:
        return {'level': 'unknown', 'reason': '结果为空'}

    total_sum = sum(scores_sorted) if sum(scores_sorted) != 0 else 1.0
    top10 = scores_sorted[:10]
    top10_ratio = sum(top10) / total_sum

    top1 = scores_sorted[0]
    top2 = scores_sorted[1] if len(scores_sorted) > 1 else None
    gap12 = (top1 - top2) if (top2 is not None) else None

    mean = dist.get('mean')
    med = dist.get('median')

    # 简单分级
    if top10_ratio >= 0.6 and mean is not None and top1 >= mean * 2:
        return {'level': 'high', 'reason': '头部高度集中且Top1显著高于均值', 'top10_ratio': top10_ratio, 'gap12': gap12}
    if top10_ratio >= 0.4:
        return {'level': 'medium', 'reason': '头部集中度较高', 'top10_ratio': top10_ratio, 'gap12': gap12}
    return {'level': 'low', 'reason': '分数分布相对分散', 'top10_ratio': top10_ratio, 'gap12': gap12}



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


@bp.route('/identification/tasks/<task_id>/report', methods=['GET'])
@require_auth
def get_identification_report(task_id: str):
    try:
        t = identification_service.get_task(task_id)
        if not t:
            return fail('任务不存在', http_code=404)
        if (not is_admin()) and t.user_id != g.user['id']:
            return fail('无权限访问该任务', http_code=403)
        if t.status != identification_service.TASK_STATUS_SUCCEEDED:
            return fail('任务未完成，无法生成报告', http_code=409)

        # 取结果（优先内存，其次 DB）
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

        # 算法元信息（来自 DB algorithms 表）
        algo_row = None
        try:
            from application.services import algorithms_service
            algo_row = algorithms_service.get_algorithm_by_key(t.algorithm_key)
        except Exception:
            algo_row = None

        # 文件元信息 + 图数据
        upload_row = uploads_service.get_upload_record(int(t.file_id))
        if not upload_row:
            return fail('文件不存在', http_code=404)

        stored_name = upload_row.get('stored_name')
        original_name = upload_row.get('original_name') or stored_name
        if not stored_name:
            return fail('文件记录不完整: stored_name', http_code=500, status='error')

        _, ext = os.path.splitext(stored_name or '')
        ext = (ext or '').lstrip('.')
        if not ext:
            _, ext2 = os.path.splitext(original_name or '')
            ext = (ext2 or '').lstrip('.')

        abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)

        # 报告生成时建议适度截断边数，避免大图阻塞（可通过 query 调整）
        max_edges = request.args.get('max_edges', default=200000, type=int)
        if max_edges is not None and max_edges <= 0:
            max_edges = None

        graph_obj = parse_graph_from_file(abs_path=abs_path, ext=ext, max_edges=max_edges)

        # TopN（默认 20）
        top_n = request.args.get('top_n', default=20, type=int)
        top_n = max(1, min(int(top_n or 20), 200))

        # 排序结果
        items = []
        for k, v in result.items():
            items.append((str(k), v, _safe_float(v, None)))
        items.sort(key=lambda x: (x[2] is not None, x[2]), reverse=True)

        top_items = items[:top_n]
        top_nodes = [it[0] for it in top_items]
        top_scores = [it[2] for it in top_items if it[2] is not None]
        all_scores = [it[2] for it in items if it[2] is not None]

        dist = _score_distribution(all_scores)
        risk = _risk_level(top_scores=top_scores, all_scores=all_scores)

        # 构建 networkx 无向图（用于最大连通分量口径指标 / 桥接点等）
        G = nx.Graph()
        for n in graph_obj.get('nodes') or []:
            nid = (n or {}).get('id')
            if nid is not None:
                G.add_node(str(nid))
        for e in graph_obj.get('edges') or []:
            s = (e or {}).get('source')
            tt = (e or {}).get('target')
            if s is None or tt is None:
                continue
            s = str(s)
            tt = str(tt)
            if s and tt:
                G.add_edge(s, tt)

        graph_metrics = _compute_graph_metrics(G, graph_obj, top_nodes=top_nodes)

        def _algo_explain(algo_key: str) -> str:
            k = (algo_key or '').strip().lower()
            if k == 'dc':
                return '度中心性：连接范围更广的节点更可能成为扩散枢纽。'
            if k == 'bc':
                return '介数中心性：位于更多最短路径上的节点更可能充当跨群体传播桥梁。'
            if k == 'cc':
                return '接近中心性：更靠近网络中心的节点信息触达更快。'
            if k == 'cr':
                return '圈比：基于圈层结构衡量节点的关键性（具体含义依赖你的实现）。'
            if k == 'hgc':
                return 'HGC：基于异质/高阶结构的关键节点识别（具体含义依赖你的实现）。'
            if k == 'mgnn-al':
                return 'MGNN_AL：基于图神经网络的学习式识别，输出为模型评分。'
            return '基于所选算法对节点进行评分排序。'

        top_nodes_detail = []
        for idx, (nid, raw_v, fv) in enumerate(top_items, start=1):
            nm = (graph_metrics.get('top_node_metrics') or {}).get(nid) or {}
            top_nodes_detail.append({
                'rank': idx,
                'node_id': nid,
                'score': fv,
                'raw_score': raw_v,
                'degree': nm.get('degree'),
                'neighbors_sample': nm.get('neighbors_sample') or [],
            })

        graph_summary = graph_metrics.get('graph_summary') or {}

        # --- 自动生成传播预测（报告页进入即展示） ---
        # 说明：传播仿真耗时与图规模相关，这里默认使用 max_edges 截断后的图。
        # 输出：
        # - propagation.multi：Top-10 联合种子传播概率图
        # - propagation.single：每个 seed 单独传播概率图（默认取 Top-3，避免过慢）
        # 确保报告输出结构稳定：即使传播计算失败，也返回可解释的空结构
        propagation = {
            'mode': 'auto',
            'seeds': [],
            'multi': {
                'graph': {
                    'nodes': [],
                    'edges': [],
                    'meta': {'nodes': 0, 'edges': 0},
                },
                'steps': [],
                'max_steps': 0,
                'error': None,
            },
        }
        try:
            k_prop = request.args.get('prop_k', default=10, type=int)
            k_prop = max(1, min(int(k_prop or 10), 50))
            num_simulations = request.args.get('prop_num_simulations', default=500, type=int)
            num_simulations = max(10, min(int(num_simulations or 500), 5000))
            edge_threshold = request.args.get('prop_edge_threshold', default=0.1, type=float)
            edge_threshold = float(edge_threshold or 0.0)
            max_edges_in_view = request.args.get('prop_top_edges', default=200, type=int)
            max_edges_in_view = max(50, min(int(max_edges_in_view or 200), 2000))

            # 种子节点：默认用 Top-K
            prop_seeds = [x.get('node_id') for x in top_nodes_detail[:k_prop] if x.get('node_id')]
            if prop_seeds:
                beta = threshhold(G)
                simulator = PropagationSimulator(G)

                multi_graph = simulator.calculate_propagation(
                    beta=beta,
                    source_nodes=prop_seeds,
                    num_simulations=num_simulations,
                )

                # 过滤 & 截断边（与前端 buildGraphFromPropagation 同思路，但后端先做一次瘦身）
                def _compact_prob_graph(pg):
                    raw_edges = pg.get('edges') or pg.get('links') or []
                    raw_nodes = pg.get('nodes') or []
                    edges2 = []
                    for e in raw_edges:
                        s = e.get('source') if isinstance(e, dict) else None
                        t2 = e.get('target') if isinstance(e, dict) else None
                        p = e.get('prob') if isinstance(e, dict) else None
                        if s is None or t2 is None:
                            continue
                        try:
                            pf = float(p)
                        except Exception:
                            pf = 0.0
                        if pf < edge_threshold:
                            continue
                        edges2.append({'source': str(s), 'target': str(t2), 'prob': pf})
                    edges2.sort(key=lambda x: x.get('prob', 0.0), reverse=True)
                    edges2 = edges2[:max_edges_in_view]

                    # 节点集合
                    node_set = set()
                    for e in edges2:
                        node_set.add(e['source'])
                        node_set.add(e['target'])
                    for n in raw_nodes:
                        nid = n.get('id') if isinstance(n, dict) else None
                        if nid is not None:
                            node_set.add(str(nid))

                    nodes2 = [{'id': nid, 'label': nid} for nid in sorted(node_set)]
                    return {
                        'graph': {
                            'nodes': nodes2,
                            'edges': [{'source': e['source'], 'target': e['target'], 'weight': e['prob']} for e in edges2],
                            'meta': {'nodes': len(nodes2), 'edges': len(edges2)},
                        },
                        'edges': edges2,
                        'beta': beta,
                        'num_simulations': num_simulations,
                        'edge_threshold': edge_threshold,
                        'top_edges': max_edges_in_view,
                    }

                # multi
                multi_compact = _compact_prob_graph(multi_graph)

                # steps：用于报告页按时间步展示传播路径（与 /identification/propagation 接口一致）
                try:
                    prop_max_steps = request.args.get('prop_max_steps', default=4, type=int)
                    prop_max_steps = max(1, min(int(prop_max_steps or 4), 20))
                except Exception:
                    prop_max_steps = 4

                steps = []
                try:
                    steps = simulator.calculate_propagation_steps(
                        beta=beta,
                        source_nodes=prop_seeds,
                        num_simulations=num_simulations,
                        max_steps=prop_max_steps,
                    )
                except Exception as _e_steps:
                    # 不阻断报告生成
                    steps = []

                # 对齐 /identification/propagation 返回格式（报告页也按同一字段取数）
                # - multi.probability_graph：原始传播概率图（可能是 map 或包含 edges/nodes 的对象）
                # - multi.steps：时间步结果（用于可视化）
                # 同时保留 compact 结果用于列表/摘要展示
                propagation = {
                    'mode': 'multi',
                    'task_id': t.task_id,
                    'file_id': t.file_id,
                    'k': k_prop,
                    'beta': beta,
                    'num_simulations': num_simulations,
                    'source_nodes': prop_seeds,
                    'multi': {
                        'probability_graph': multi_graph,
                        # 兼容 calculate_propagation_steps 可能返回 {"steps": [...]} 的情况
                        'steps': (steps.get('steps') if isinstance(steps, dict) else steps) or [],
                        'max_steps': prop_max_steps,
                        # 兼容旧前端/现有 compact 字段
                        'graph': multi_compact.get('graph'),
                        'edges': multi_compact.get('edges'),
                        'edge_threshold': multi_compact.get('edge_threshold'),
                        'top_edges': multi_compact.get('top_edges'),
                        'error': None,
                    },
                }

                # single seeds：默认 Top-3
                single_n = request.args.get('prop_single_n', default=3, type=int)
                single_n = max(0, min(int(single_n or 3), 10))
                if single_n > 0:
                    single = {}
                    for seed in prop_seeds[:single_n]:
                        pg = simulator.calculate_propagation(
                            beta=beta,
                            source_nodes=[seed],
                            num_simulations=num_simulations,
                        )
                        single[str(seed)] = _compact_prob_graph(pg)
                    propagation['single'] = single
        except Exception as _e_prop:
            try:
                current_app.logger.exception('报告传播预测生成失败: %s', _e_prop)
            except Exception:
                pass
            propagation['multi']['error'] = str(_e_prop)

        # --- 治理建议（引入传播预测 + 桥接点/介数/割点） ---
        top10_ratio = (risk or {}).get('top10_ratio')
        largest_comp_ratio = graph_summary.get('largest_component_ratio')

        def _priority_from_risk(level: str) -> str:
            if level == 'high':
                return 'P0'
            if level == 'medium':
                return 'P1'
            if level == 'low':
                return 'P2'
            return 'P2'

        priority = _priority_from_risk((risk or {}).get('level'))

        # --- 治理建议：工单化 + evidence（风险+结构+传播+桥接点/割点） ---
        def _op(type_: str, desc: str):
            return {'type': type_, 'desc': desc}

        def _evidence_base():
            return {
                'risk': risk,
                'graph': {
                    **(graph_summary or {}),
                    'largest_component_metrics': graph_metrics.get('largest_component_metrics') or {},
                },
                'propagation': {
                    'has': propagation is not None,
                    'edge_threshold': (propagation or {}).get('multi', {}).get('edge_threshold') if propagation else None,
                    'top_edges': (propagation or {}).get('multi', {}).get('top_edges') if propagation else None,
                }
            }

        # 1) 结构侧：最大连通分量上的桥接点/割点/桥
        bridges_info = None
        betweenness_top = []
        articulation_points = []
        try:
            if G.number_of_nodes() > 0:
                largest_cc = max(nx.connected_components(G), key=len)
                H = G.subgraph(largest_cc).copy()

                # betweenness：只取 Top-N，避免过慢
                bet_n = request.args.get('gov_bet_top_n', default=10, type=int)
                bet_n = max(3, min(int(bet_n or 10), 50))
                # NOTE: betweenness_centrality 对大图会慢；截断 max_edges 后一般可接受
                bc = nx.betweenness_centrality(H, normalized=True)
                betweenness_top = [
                    {'node_id': str(k), 'betweenness': float(v)}
                    for k, v in sorted(bc.items(), key=lambda kv: kv[1], reverse=True)[:bet_n]
                ]

                # articulation points
                ap_n = request.args.get('gov_ap_top_n', default=10, type=int)
                ap_n = max(0, min(int(ap_n or 10), 50))
                articulation_points = [str(x) for x in nx.articulation_points(H)]
                if ap_n > 0:
                    articulation_points = articulation_points[:ap_n]

                # bridges
                br_n = request.args.get('gov_bridge_top_n', default=20, type=int)
                br_n = max(0, min(int(br_n or 20), 200))
                bridges = []
                if br_n > 0:
                    for u, v in nx.bridges(H):
                        bridges.append({'source': str(u), 'target': str(v)})
                        if len(bridges) >= br_n:
                            break
                bridges_info = {
                    'basis': 'largest_connected_component',
                    'betweenness_top': betweenness_top,
                    'articulation_points': articulation_points,
                    'bridges': bridges,
                }
        except Exception:
            bridges_info = None

        # 2) 传播侧：高概率边（来自 propagation.multi.edges）
        prop_top_edges = []
        prop_nodes_focus = []
        try:
            edges2 = (propagation or {}).get('multi', {}).get('edges') if propagation else None
            if isinstance(edges2, list) and edges2:
                pe_n = request.args.get('gov_prop_edges_n', default=20, type=int)
                pe_n = max(5, min(int(pe_n or 20), 200))
                prop_top_edges = edges2[:pe_n]
                node_set = set()
                for e in prop_top_edges:
                    node_set.add(str(e.get('source')))
                    node_set.add(str(e.get('target')))
                prop_nodes_focus = sorted(node_set)
        except Exception:
            prop_top_edges = []
            prop_nodes_focus = []

        # 3) 组装 actions
        actions = []

        # 辅助：Top 节点列表
        top3 = [x.get('node_id') for x in top_nodes_detail[:3] if x.get('node_id')]
        top10 = [x.get('node_id') for x in top_nodes_detail[:10] if x.get('node_id')]

        # P0/P1：Top 节点处置（强绑定风险）
        if priority == 'P0':
            actions.append({
                'priority': 'P0',
                'title': '对Top节点执行“人工复核 + 限制转发/降权 + 标记高风险”，必要时升级禁言/封禁',
                'targets': {
                    'nodes': top3,
                    'scope': 'top_nodes',
                },
                'operations': [
                    _op('生成工单', '为Top-3节点生成处置工单（P0），进入人工复核流程。'),
                    _op('人工复核', '核验Top-3节点主体/账号真实性、异常行为与传播上下文。'),
                    _op('标记为高风险', '对Top-3节点添加高风险标签，进入重点监控队列。'),
                    _op('限制转发', '对Top-3节点及其1跳邻域设置转发/扩散限制（临时策略）。'),
                    _op('降权', '对Top-3节点内容/触达进行降权，降低外溢扩散。'),
                    _op('发告警', '向治理负责人推送P0告警，要求在规定时限内完成处置闭环。'),
                    _op('禁言', '若复核确认高风险且持续扩散，执行禁言（可配置时长）。'),
                    _op('封禁', '若确认恶意或严重违规，执行封禁并留存证据。'),
                ],
                'reason': '风险高：头部集中且Top节点对扩散贡献显著，优先处置可快速降低总体风险。',
                'evidence': {
                    **_evidence_base(),
                    'top_nodes': top_nodes_detail[:3],
                    'bridges': bridges_info,
                    'propagation_top_edges': prop_top_edges,
                },
            })
        elif priority == 'P1':
            actions.append({
                'priority': 'P1',
                'title': '对Top节点执行“抽样人工复核 + 监测 + 必要时限制转发/降权”',
                'targets': {
                    'nodes': top10,
                    'scope': 'top_nodes',
                },
                'operations': [
                    _op('生成工单', '为Top-10节点生成处置工单（P1），优先处理Top-5。'),
                    _op('人工复核', '对Top-10节点进行抽样核验（建议Top-5全量复核）。'),
                    _op('标记为高风险', '对Top节点加入重点关注名单（风险标签可按复核结果更新）。'),
                    _op('发告警', '当Top节点分数/排名快速上升时触发告警。'),
                    _op('限制转发', '对Top节点触发阈值时启用转发限制。'),
                    _op('降权', '对Top节点触发阈值时启用降权策略。'),
                ],
                'reason': '风险中：存在头部集中趋势，先控Top节点并建立监测闭环。',
                'evidence': {
                    **_evidence_base(),
                    'top_nodes': top_nodes_detail[:10],
                    'bridges': bridges_info,
                    'propagation_top_edges': prop_top_edges,
                },
            })
        else:
            actions.append({
                'priority': 'P2',
                'title': '持续监测：关注Top节点与传播高概率链路变化，必要时升级处置',
                'targets': {
                    'nodes': top10[:5],
                    'scope': 'top_nodes',
                },
                'operations': [
                    _op('生成工单', '为Top节点生成观察工单（P2），定期复核。'),
                    _op('发告警', '当Top10占比/Top1突出度上升时自动升级告警。'),
                    _op('标记为高风险', '对进入Top节点队列的新节点自动打标并进入观察。'),
                ],
                'reason': '风险低：分布相对分散，优先监测与趋势预警。',
                'evidence': {
                    **_evidence_base(),
                    'top_nodes': top_nodes_detail[:10],
                    'bridges': bridges_info,
                    'propagation_top_edges': prop_top_edges,
                },
            })

        # P0/P1：结构阻断（桥接点/割点）
        if bridges_info and (betweenness_top or articulation_points):
            focus_nodes = []
            focus_nodes.extend([x.get('node_id') for x in betweenness_top[:5] if x.get('node_id')])
            focus_nodes.extend(articulation_points[:5])
            # 去重
            seen = set()
            focus_nodes = [x for x in focus_nodes if x and (x not in seen and not seen.add(x))]

            actions.append({
                'priority': 'P0' if priority == 'P0' else 'P1',
                'title': '针对桥接节点/割点进行“结构性阻断”以降低跨社区扩散',
                'targets': {
                    'nodes': focus_nodes,
                    'scope': 'bridge_nodes_and_articulation_points',
                },
                'operations': [
                    _op('生成工单', '生成“结构阻断”专项工单，优先处理桥接节点与割点。'),
                    _op('人工复核', '复核这些节点的跨社区连接与传播行为。'),
                    _op('限制转发', '对桥接节点启用更严格的转发限制，防止跨社区扩散。'),
                    _op('降权', '对桥接节点的内容曝光/推荐进行降权。'),
                    _op('发告警', '当桥接节点参与高概率传播边时触发告警。'),
                    _op('标记为高风险', '对高介数/割点节点加风险标识，纳入重点监控。'),
                ],
                'reason': '桥接节点/割点通常承担跨群体传播通道，结构性干预往往比单点处置更有效。',
                'evidence': {
                    **_evidence_base(),
                    'bridges': bridges_info,
                },
            })

        # P1：传播链路联动处置（高概率边）
        if prop_top_edges:
            actions.append({
                'priority': 'P0' if priority == 'P0' else 'P1',
                'title': '对传播预测中“高概率链路”两端节点进行联动处置',
                'targets': {
                    'nodes': prop_nodes_focus,
                    'scope': 'propagation_top_edges',
                    'edges_preview': prop_top_edges,
                },
                'operations': [
                    _op('生成工单', '生成“传播链路联动处置”工单，按边概率从高到低处理。'),
                    _op('发告警', '当高概率边持续出现或概率升高时告警升级。'),
                    _op('限制转发', '对高概率边两端节点启用联动限制，减少链路传播效率。'),
                    _op('降权', '对链路两端节点进行联动降权，降低扩散范围。'),
                    _op('标记为高风险', '对高频出现于高概率边的节点打标。'),
                ],
                'reason': '传播预测显示部分链路具有更高扩散概率，联动处置可直接降低传播效率。',
                'evidence': {
                    **_evidence_base(),
                    'propagation_top_edges': prop_top_edges,
                },
            })

        # 最大连通分量占比高时的补充建议
        if isinstance(largest_comp_ratio, (int, float)) and largest_comp_ratio >= 0.8:
            actions.append({
                'priority': 'P1' if priority == 'P0' else priority,
                'title': '针对最大连通分量进行范围治理（集中干预）',
                'targets': {
                    'component': 'largest',
                    'scope': 'largest_component',
                },
                'operations': [
                    _op('生成工单', '生成“最大连通分量集中治理”工单。'),
                    _op('发告警', '当最大分量占比持续升高时告警升级。'),
                    _op('限制转发', '在最大分量覆盖范围内启用扩散限制策略（可按社区分层）。'),
                    _op('降权', '对最大分量内扩散链路进行整体降权。'),
                    _op('标记为高风险', '对最大分量内高影响节点批量打标。'),
                ],
                'reason': '最大连通分量占比高，扩散主要集中在单一主场，集中干预收益更高。',
                'evidence': {
                    **_evidence_base(),
                },
            })

        # --- 模板化章节 sections ---
        algo_name = (algo_row or {}).get('name') if isinstance(algo_row, dict) else None
        algo_type = (algo_row or {}).get('type') if isinstance(algo_row, dict) else None
        algo_desc = (algo_row or {}).get('description') if isinstance(algo_row, dict) else None

        executive_text = (
            f"综合研判：风险等级为{(risk or {}).get('level') or 'unknown'}，{(risk or {}).get('reason') or ''}。"
            f"建议优先级{priority}，优先处置Top节点并对其邻域扩散进行控制。"
        )

        lcc_metrics = graph_metrics.get('largest_component_metrics') or {}

        # --- 按你确认的 3 大模块组织报告 ---
        sections = [
            {
                'id': 'network_overview',
                'title': '网络概览',
                'narrative': (
                    '平均路径长度/聚类系数等指标按“最大连通分量”口径计算。'
                ),
                'data': {
                    'file': {
                        'original_name': upload_row.get('original_name') or original_name,
                        'stored_name': upload_row.get('stored_name'),
                        'file_id': t.file_id,
                    },
                    'graph': graph_obj,
                    'metrics': {
                        **(graph_summary or {}),
                        'largest_component_metrics': lcc_metrics,
                    },
                },
            },
            {
                'id': 'key_nodes_and_propagation',
                'title': '关键节点与潜在传播路径',
                'narrative': (
                    '默认展示识别结果 Top-10 关键节点，并自动生成基于 Top-10 种子的传播预测。'
                ),
                'data': {
                    'top_nodes': top_nodes_detail[:10],
                    'propagation': propagation,
                },
            },
            {
                'id': 'governance_actions',
                'title': '治理建议与处置方案',
                'narrative': (
                    '建议结合风险等级、网络结构（桥接点/割点）与传播预测（高概率链路）执行处置。'
                ),
                'data': {
                    'priority': priority,
                    'actions': actions,
                },
            },
        ]

        report = {
            'meta': {
                'task_id': t.task_id,
                'file_id': t.file_id,
                'algorithm_key': t.algorithm_key,
                'params': t.params or {},
                'algo': {
                    'name': algo_name,
                    'type': algo_type,
                    'description': algo_desc,
                },
                'file': {
                    'original_name': upload_row.get('original_name'),
                    'stored_name': upload_row.get('stored_name'),
                    'size_bytes': upload_row.get('size_bytes'),
                    'visibility': upload_row.get('visibility'),
                },
                'time': {
                    'created_at': getattr(t.created_at, 'isoformat', lambda: None)() if hasattr(t.created_at, 'isoformat') else t.created_at,
                    'started_at': getattr(t.started_at, 'isoformat', lambda: None)() if hasattr(t.started_at, 'isoformat') else t.started_at,
                    'ended_at': getattr(t.ended_at, 'isoformat', lambda: None)() if hasattr(t.ended_at, 'isoformat') else t.ended_at,
                },
                'settings': {
                    'top_n': top_n,
                    'max_edges': max_edges,
                }
            },
            # 保留 summary 以兼容旧前端（但前端后续建议用 sections）
            'summary': {
                'risk': risk,
                'score_distribution': dist,
                **graph_summary,
                'algo_explain': _algo_explain(t.algorithm_key),
                'priority': priority,
            },
            'top_nodes': top_nodes_detail,
            'sections': sections,
        }

        return ok({'task_id': t.task_id, 'report': report})

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except FileNotFoundError:
        return fail('文件不存在(磁盘)', http_code=404)
    except ValueError as ve:
        return fail(str(ve), http_code=400)
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
        max_steps = data.get('max_steps', 4)
        return_steps = data.get('return_steps', True)

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

        # steps 参数校验
        try:
            max_steps = int(max_steps)
        except Exception:
            max_steps = 4
        max_steps = max(1, min(max_steps, 20))

        return_steps = bool(return_steps)

        if mode == 'single':
            graphs = {}
            steps_by_seed = {}
            for seed in topk_nodes:
                graphs[seed] = simulator.calculate_propagation(
                    beta=beta,
                    source_nodes=[seed],
                    num_simulations=num_simulations,
                )
                if return_steps:
                    steps_by_seed[seed] = simulator.calculate_propagation_steps(
                        beta=beta,
                        source_nodes=[seed],
                        num_simulations=num_simulations,
                        max_steps=max_steps,
                    )

            payload = {
                'mode': 'single',
                'task_id': task_id,
                'file_id': t.file_id,
                'k': k,
                'beta': beta,
                'num_simulations': num_simulations,
                'topk_nodes': topk_nodes,
                'probability_graphs': graphs,
            }
            if return_steps:
                payload['steps_by_seed'] = steps_by_seed
                payload['max_steps'] = max_steps
            return ok(payload)

        # mode == 'multi'
        prob_graph = simulator.calculate_propagation(
            beta=beta,
            source_nodes=topk_nodes,
            num_simulations=num_simulations,
        )

        payload = {
            'mode': 'multi',
            'task_id': task_id,
            'file_id': t.file_id,
            'k': k,
            'beta': beta,
            'num_simulations': num_simulations,
            'source_nodes': topk_nodes,
            'probability_graph': prob_graph,
        }
        if return_steps:
            payload['steps'] = simulator.calculate_propagation_steps(
                beta=beta,
                source_nodes=topk_nodes,
                num_simulations=num_simulations,
                max_steps=max_steps,
            )
            payload['max_steps'] = max_steps

        return ok(payload)

    except Error as e:
        return fail('数据库错误: ' + str(e), http_code=500, status='error')
    except Exception as e:
        return fail('系统错误: ' + str(e), http_code=500, status='error')
