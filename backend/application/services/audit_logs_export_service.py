from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from application.repositories import audit_logs_repo


_EXPORT_COLUMNS: List[Tuple[str, str]] = [
    ("id", "ID"),
    ("created_at", "时间"),
    ("actor_user_id", "操作者ID"),
    ("action", "动作"),
    ("target_type", "目标类型"),
    ("target_id", "目标ID"),
    ("detail_json", "详情"),
]


def _normalize_cell_value(v: Any) -> str:
    if v is None:
        return ""
    # MySQL connector 可能返回 datetime
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, default=str)
    return str(v)


def _maybe_pretty_json(s: Any) -> str:
    if s is None:
        return ""
    if isinstance(s, (dict, list)):
        return json.dumps(s, ensure_ascii=False, default=str)
    if not isinstance(s, str):
        return str(s)
    try:
        obj = json.loads(s)
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return s


def fetch_export_rows(
    action: Optional[str] = None,
    keyword: Optional[str] = None,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    limit: int = 50000,
) -> List[Dict[str, Any]]:
    return audit_logs_repo.export_audit_logs(
        action=action,
        keyword=keyword,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )


def generate_csv_bytes(rows: List[Dict[str, Any]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([title for _, title in _EXPORT_COLUMNS])

    for r in rows:
        # detail_json 尽量做成可读的单行 JSON
        r = dict(r or {})
        r["detail_json"] = _maybe_pretty_json(r.get("detail_json"))
        writer.writerow([_normalize_cell_value(r.get(key)) for key, _ in _EXPORT_COLUMNS])

    return buf.getvalue().encode("utf-8-sig")


def generate_excel_bytes(rows: List[Dict[str, Any]]) -> bytes:
    """生成 xlsx bytes（依赖 openpyxl）。"""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "audit_logs"

    ws.append([title for _, title in _EXPORT_COLUMNS])

    for r in rows:
        r = dict(r or {})
        r["detail_json"] = _maybe_pretty_json(r.get("detail_json"))
        ws.append([_normalize_cell_value(r.get(key)) for key, _ in _EXPORT_COLUMNS])

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()

