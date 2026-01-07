from __future__ import annotations
from typing import Any, Dict
from .registry import ProgressCallback, IsCancelled

def run(abs_path: str, params: Dict[str, Any], progress_cb: ProgressCallback, is_cancelled: IsCancelled) -> Dict[str, Any]:
    """
    算法包装函数：将你的现有算法嵌入系统框架。
    """
    # 1. 报告初始进度
    progress_cb(10, 'loading', '正在初始化...')
    if is_cancelled():
        return {}

    # 2. 加载图
    from application.algorithms.utils import load_graph
    G = load_graph(abs_path)
    if is_cancelled():
        return {}

    # 3. 准备进度提示（可选）
    n = G.number_of_nodes()
    progress_cb(30, 'computing', f'图加载完成，共 {n} 个节点，开始执行核心算法...')

    # 4. 【核心】在这里调用你的现有算法函数
    # 假设你的算法函数名为 `my_existing_algorithm`，它接收一个 networkx.Graph 对象
    # 并返回 {node_id: node_value}
    from application.algorithms.my_algo_module import cr # 导入你的算法模块
    # 或者，如果你的算法代码直接写在这个文件里，直接调用函数
    result_dict = cr.compute_cycle_ratio(G)

    # 5. 检查取消和进度
    if is_cancelled():
        return {}
    progress_cb(90, 'finalizing', '核心算法计算完成，正在格式化结果...')

    # 6. 确保结果格式正确（关键步骤）
    # 系统要求键为字符串，值为浮点数/整数。如果你的算法已满足，通常无需处理。
    # 这是一个安全的类型转换检查：
    formatted_result = {}
    for node_id, value in result_dict.items():
        formatted_result[str(node_id)] = float(value)  # 确保键是字符串，值是浮点数
        # 如果 node_value 可能是 complex 或其它类型，你需要先在这里做转换

    # 7. 返回最终结果
    progress_cb(100, 'done', '计算完成')
    return formatted_result