import os
import sys
import importlib
from typing import Any, Dict, Optional

# 项目根目录（backend 的上一级）
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def _ensure_root_in_sys_path():
    if ROOT_DIR not in sys.path:
        sys.path.append(ROOT_DIR)


def fetch_html(url: str) -> str:
    _ensure_root_in_sys_path()
    pachong = importlib.import_module('pachong')
    return pachong.fetch_html(url)


def parse_today_section(html: str, base_url: str, max_items: int) -> Optional[Dict[str, Any]]:
    _ensure_root_in_sys_path()
    pachong = importlib.import_module('pachong')
    return pachong.parse_today_section(html, base_url=base_url, max_items=max_items)


def parse_lianhe_section(html: str, base_url: str, max_items: int) -> Optional[Dict[str, Any]]:
    _ensure_root_in_sys_path()
    pachong = importlib.import_module('pachong')
    return pachong.parse_LianHePiYao(html, base_url=base_url, max_items=max_items)

