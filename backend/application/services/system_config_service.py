"""系统配置服务层：提供默认值合并、读取与写入。"""
from typing import Dict, List, Optional

from application.repositories import system_config_repo

# 系统级默认配置（如数据库没有配置时使用）
DEFAULT_CONFIG: Dict[str, str] = {
    # 上传相关
    "max_upload_mb": "20",  # 单位 MB

    # 图计算相关
    "max_edges_limit": "10000",  # 最大边数上限

    # 识别任务
    "default_algorithm_key": "",  # 系统推荐/默认算法

    # 模块开关
    "enable_network_visualization": "1",  # 1=开启 0=关闭
    "enable_debunk_module": "1",          # 联合辟谣模块
}


def get_system_config(keys: Optional[List[str]] = None) -> Dict[str, str]:
    """读取系统配置，自动合并默认值。"""
    db_cfg = system_config_repo.get_config(keys)

    result: Dict[str, str] = {}
    target_keys = keys or list(DEFAULT_CONFIG.keys())
    for k in target_keys:
        if k in db_cfg:
            result[k] = db_cfg[k]
        elif k in DEFAULT_CONFIG:
            result[k] = DEFAULT_CONFIG[k]
    return result


def update_system_config(new_cfg: Dict[str, str], updated_by: Optional[int] = None) -> None:
    """写入系统配置，仅写入发生变化的键。"""
    if not isinstance(new_cfg, dict):
        raise ValueError("配置必须是字典")

    # 过滤掉 None / 空字符串
    filtered = {k: v for k, v in new_cfg.items() if v is not None and v != ""}
    if not filtered:
        return

    system_config_repo.set_config_items(filtered, updated_by=updated_by)
