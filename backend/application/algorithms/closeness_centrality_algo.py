from __future__ import annotations

from typing import Any, Dict

from .registry import IsCancelled, ProgressCallback


def run(
    abs_path: str,
    params: Dict[str, Any],
    progress_cb: ProgressCallback,
    is_cancelled: IsCancelled,
) -> Dict[str, Any]:
    params = params or {}

    progress_cb(5, 'loading', '读取边列表并构建图')
    if is_cancelled():
        return {}

    from application.algorithms.utils import load_graph

    G = load_graph(abs_path)

    if is_cancelled():
        return {}

    n = G.number_of_nodes()
    m = G.number_of_edges()
    progress_cb(30, 'computing', f'开始计算接近中心性（节点={n}，边={m}）')

    if n == 0:
        progress_cb(100, 'done', '空图，无需计算')
        return {}

    import networkx as nx

    if is_cancelled():
        return {}

    cc = nx.closeness_centrality(G)

    if is_cancelled():
        return {}

    progress_cb(90, 'finalizing', '格式化结果')

    out: Dict[str, Any] = {}
    for node_id, value in cc.items():
        out[str(node_id)] = float(value)

    progress_cb(100, 'done', '计算完成')
    return out

