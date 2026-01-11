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

    progress_cb(10, 'loading', '正在读取多层网络并初始化...')
    if is_cancelled():
        return {}

    from application.algorithms.utils import load_multilayer_graph

    Gs = load_multilayer_graph(abs_path)

    if is_cancelled():
        return {}

    total_layers = len(Gs) if isinstance(Gs, (list, tuple)) else 1
    progress_cb(30, 'computing', f'图加载完成，共 {total_layers} 层，开始执行 MGNN_AL 推理...')

    if is_cancelled():
        return {}

    from application.algorithms.my_algo_module.MGNN_AL import mgnn_al
    from application.algorithms.my_algo_module.MGNN_AL.Model import CombinedModel

    
    result_dict = mgnn_al.MGNN_AL(Gs)

    if is_cancelled():
        return {}

    progress_cb(90, 'finalizing', '推理完成，正在格式化结果...')

    formatted_result: Dict[str, Any] = {}
    for node_id, value in result_dict.items():
        formatted_result[str(node_id)] = float(value)

    progress_cb(100, 'done', '计算完成')
    return formatted_result

