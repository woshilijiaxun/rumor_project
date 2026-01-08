"""系统配置服务层：提供默认值合并、读取与写入。"""
from typing import Dict, List, Optional, Any

from application.repositories import system_config_repo
from application.services.audit_logs_service import write_log
from application.services.audit_context import sanitize_detail

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


def update_system_config(
    new_cfg: Dict[str, str],
    updated_by: Optional[int] = None,
    actor_meta: Optional[Dict[str, Any]] = None,
) -> None:
    """写入系统配置，并记录审计日志（关键操作）。

    - 仅写入发生变化的键
    - 日志记录 before/after（仅本次更新涉及的 keys）
    """
    if not isinstance(new_cfg, dict):
        raise ValueError("配置必须是字典")

    # 过滤掉 None / 空字符串（保持你原逻辑：空字符串视为不写入）
    filtered = {k: v for k, v in new_cfg.items() if v is not None and v != ""}
    if not filtered:
        return

    keys = list(filtered.keys())

    # before：取当前配置（含默认值）
    before_cfg: Dict[str, str] = {}
    try:
        before_cfg = get_system_config(keys)
    except Exception:
        before_cfg = {}

    try:
        system_config_repo.set_config_items(filtered, updated_by=updated_by)

        after_cfg: Dict[str, str] = {}
        try:
            after_cfg = get_system_config(keys)
        except Exception:
            after_cfg = {k: str(v) for k, v in filtered.items()}

        try:
            write_log(
                actor_user_id=updated_by,
                action='CONFIG_UPDATE',
                target_type='system_config',
                target_id=None,
                detail=sanitize_detail({
                    'result': 'success',
                    'updated_keys': keys,
                    'before': before_cfg,
                    'after': after_cfg,
                    'actor': actor_meta or {},
                }),
            )
        except Exception:
            pass

    except Exception as e:
        try:
            write_log(
                actor_user_id=updated_by,
                action='CONFIG_UPDATE',
                target_type='system_config',
                target_id=None,
                detail=sanitize_detail({
                    'result': 'fail',
                    'updated_keys': keys,
                    'before': before_cfg,
                    'after': {k: str(v) for k, v in filtered.items()},
                    'error': str(e),
                    'actor': actor_meta or {},
                }),
            )
        except Exception:
            pass
        raise
