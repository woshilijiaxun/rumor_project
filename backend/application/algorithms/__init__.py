"""算法实现包。

放置真实识别算法代码的推荐位置。

约定：
- 每个算法实现提供一个 runner（函数或类），统一签名：
  run(abs_path: str, params: dict, progress_cb: callable, is_cancelled: callable) -> dict
- 返回值必须是 map：{node_id: node_value}

注意：本包只放算法“计算逻辑”，不要直接依赖 Flask 的 request/current_app。
"""

from .registry import AlgorithmRegistry, registry  # noqa: F401

