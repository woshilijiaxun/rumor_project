"""度中心性（Degree Centrality）算法。

输入文件：txt，每行格式为：
  node1 node2
表示 node1 与 node2 之间存在连接。

输出：
  {node_id: degree_centrality}
其中 degree_centrality = degree/(n-1)（无向图归一化度中心性）。

实现要点：
- 复用你现有的图加载方法：application.algorithms.utils.load_graph
- 支持任务进度回调 progress_cb
- 支持取消 is_cancelled

params（可选）：
- normalized: bool = True  是否归一化到 [0,1]
- include_isolated: bool = True  是否在输出中包含孤立点（默认包含；当前输入边表不含孤立点信息时，该选项无影响）
"""

from __future__ import annotations

from typing import Any, Dict

from .registry import ProgressCallback, IsCancelled


def run(abs_path: str, params: Dict[str, Any], progress_cb: ProgressCallback, is_cancelled: IsCancelled) -> Dict[str, Any]:
    params = params or {}
    normalized = bool(params.get('normalized', True))

    progress_cb(5, 'loading', '读取边列表并构建图')
    if is_cancelled():
        return {}

    # 复用现有建图逻辑（无向图）
    # utils.py 里依赖 networkx，这里也依赖同一环境
    from application.algorithms.utils import load_graph

    G = load_graph(abs_path)

    if is_cancelled():
        return {}

    n = G.number_of_nodes()
    m = G.number_of_edges()
    progress_cb(40, 'computing', f'开始计算度中心性（节点={n}，边={m}）')

    # 计算度
    degrees = dict(G.degree())

    # 归一化：除以 (n-1)
    denom = (n - 1) if (normalized and n > 1) else 1

    out: Dict[str, Any] = {}
    # 迭代节点输出
    nodes = list(G.nodes())
    total = len(nodes)

    for i, node in enumerate[Any](nodes):
        if is_cancelled():
            return {}
        deg = degrees.get(node, 0)
        val = float(deg) / float(denom)
        out[str(node)] = val

        # 进度：40 -> 90
        if total > 0 and (i + 1) % max(1, total // 20) == 0:
            p = 40 + int((i + 1) / total * 50)
            progress_cb(min(90, p), 'computing', f'计算中：{i + 1}/{total}')

    progress_cb(95, 'finalizing', '整理结果')
    return out

