from __future__ import annotations

from typing import Any, Dict, Optional


def safe_truncate(v: Any, max_len: int = 500) -> Any:
    try:
        s = str(v)
        if len(s) <= max_len:
            return v
        return s[:max_len] + '…'
    except Exception:
        return None


def sanitize_detail(detail: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """脱敏与限长：避免把 token/password 等敏感信息写入审计日志。"""
    if detail is None:
        return None
    if not isinstance(detail, dict):
        return {"_raw": safe_truncate(detail)}

    sensitive_keys = {
        'password', 'passwd', 'pwd',
        'token', 'authorization', 'secret', 'api_key', 'apikey',
    }

    out: Dict[str, Any] = {}
    for k, v in detail.items():
        try:
            lk = str(k).lower()
        except Exception:
            lk = ''

        if any(sk in lk for sk in sensitive_keys):
            out[k] = '***'
            continue

        if isinstance(v, dict):
            out[k] = sanitize_detail(v)
        elif isinstance(v, list):
            out[k] = [safe_truncate(x) for x in v][:200]
        else:
            out[k] = safe_truncate(v)

    return out

