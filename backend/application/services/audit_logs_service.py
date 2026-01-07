from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from application.repositories import audit_logs_repo


def write_log(
    actor_user_id: Optional[int],
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> int:
    return audit_logs_repo.insert_audit_log(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )


def query_logs(
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
    keyword: Optional[str] = None,
) -> Dict[str, Any]:
    items, total = audit_logs_repo.list_audit_logs(
        page=page,
        page_size=page_size,
        action=action,
        keyword=keyword,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 1,
    }

