from typing import Dict, Optional, List
from flask import g
from application.repositories import algorithms_repo as repo


def list_algorithms_paginated(page: int, page_size: int) -> Dict:
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 10), 1), 100)
    offset = (page - 1) * page_size
    total = repo.count_algorithms()
    items = repo.list_algorithms(offset=offset, limit=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def create_algorithm(name: str, algo_key: str, description: str, algo_type: str, status: str) -> int:
    user_id = None
    try:
        user_id = g.user['id']  # 由 require_auth 注入
    except Exception:
        user_id = None
    return repo.create_algorithm(user_id, name, algo_key, description, algo_type, status)


def get_algorithm(algo_id: int) -> Optional[Dict]:
    return repo.get_algorithm(algo_id)


def get_algorithm_by_key(algo_key: str) -> Optional[Dict]:
    return repo.get_algorithm_by_key(algo_key)


def update_algorithm(algo_id: int, name: Optional[str], algo_key: Optional[str], description: Optional[str], algo_type: Optional[str], status: Optional[str]) -> None:
    fields: Dict[str, object] = {}
    if name is not None:
        fields['name'] = name.strip()
    if algo_key is not None:
        fields['algo_key'] = algo_key.strip()
    if description is not None:
        fields['description'] = description.strip()
    if algo_type is not None:
        fields['type'] = algo_type.strip()
    if status is not None:
        fields['status'] = status
    repo.update_algorithm_fields(algo_id, fields)


def delete_algorithm(algo_id: int) -> None:
    repo.delete_algorithm(algo_id)


def list_all_algorithms() -> List[Dict]:
    total = repo.count_algorithms()
    if total <= 0:
        return []
    return repo.list_algorithms(offset=0, limit=min(total, 10000))
