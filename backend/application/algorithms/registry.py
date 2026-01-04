from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


ProgressCallback = Callable[[int, str, str], None]
IsCancelled = Callable[[], bool]


@dataclass
class AlgorithmSpec:
    """算法运行时描述。"""

    algo_key: str
    name: str
    runner: Callable[[str, Dict[str, Any], ProgressCallback, IsCancelled], Dict[str, Any]]


class AlgorithmRegistry:
    """方案2：稳定键 algo_key -> runner。

    - 前端提交 algorithm_key(algo_key)
    - 后端识别任务执行时通过 algo_key 查找 runner

    这样不依赖数据库自增 id，换库/迁移不影响。
    """

    def __init__(self):
        self._specs_by_key: Dict[str, AlgorithmSpec] = {}

    def register_key(self, algo_key: str, name: str, runner):
        if not algo_key:
            raise ValueError('algo_key 不能为空')
        k = str(algo_key).strip()
        if not k:
            raise ValueError('algo_key 不能为空')
        self._specs_by_key[k] = AlgorithmSpec(algo_key=k, name=name or k, runner=runner)

    def get_by_key(self, algo_key: str) -> Optional[AlgorithmSpec]:
        if not algo_key:
            return None
        return self._specs_by_key.get(str(algo_key).strip())

    def list_keys(self):
        return sorted(self._specs_by_key.keys())


registry = AlgorithmRegistry()


# --- 在这里按 algo_key 注册你的算法实现 ---
try:
    from .example_textline_algo import run as _example_run
    from .degree_centrality_algo import run as _degree_run
    from .hgc_algo import run as _hgc_run

    # 该 key 必须与你数据库 algorithms.algo_key 一致
    registry.register_key('example_textline_algo', '示例-按行读取', _example_run)
    registry.register_key('dc', '度中心性', _degree_run)
    registry.register_key('hgc', 'HGC算法', _hgc_run)
except Exception:
    pass


