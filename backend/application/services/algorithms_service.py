from typing import Dict, Optional, List, Any

from flask import g

from application.repositories import algorithms_repo as repo
from application.services.audit_logs_service import write_log
from application.services.audit_context import sanitize_detail


def list_algorithms_paginated(page: int, page_size: int) -> Dict:
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 10), 1), 100)
    offset = (page - 1) * page_size
    total = repo.count_algorithms()
    items = repo.list_algorithms(offset=offset, limit=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def update_algorithms_order(
    order_ids: List[int],
    actor_meta: Optional[Dict[str, Any]] = None,
) -> None:
    # order_ids: 前端提交的算法 id 顺序（从上到下）
    ids: List[int] = []
    for v in (order_ids or []):
        try:
            ids.append(int(v))
        except Exception:
            continue

    if not ids:
        return

    pairs = [(algo_id, idx) for idx, algo_id in enumerate(ids)]
    repo.bulk_update_sort_order(pairs)

    # 审计日志（尽量不影响主流程）
    try:
        actor_user_id = None
        try:
            actor_user_id = g.user['id']
        except Exception:
            actor_user_id = None

        write_log(
            actor_user_id=actor_user_id,
            action='ALGORITHM_ORDER_UPDATE',
            target_type='algorithm',
            target_id=None,
            detail=sanitize_detail({
                'result': 'success',
                'extra': {
                    'count': len(ids),
                    'order_ids': ids,
                },
                'actor': actor_meta or {},
            }),
        )
    except Exception:
        pass


def create_algorithm(
    name: str,
    algo_key: str,
    description: str,
    algo_type: str,
    status: str,
    actor_meta: Optional[Dict[str, Any]] = None,
) -> int:
    actor_user_id = None
    try:
        actor_user_id = g.user['id']  # 由 require_auth 注入
    except Exception:
        actor_user_id = None

    try:
        algo_id = repo.create_algorithm(actor_user_id, name, algo_key, description, algo_type, status)
        try:
            write_log(
                actor_user_id=actor_user_id,
                action='ALGORITHM_CREATE',
                target_type='algorithm',
                target_id=str(algo_id),
                detail=sanitize_detail({
                    'result': 'success',
                    'extra': {
                        'algo_key': algo_key,
                        'name': name,
                        'type': algo_type,
                        'status': status,
                    },
                    'actor': actor_meta or {},
                }),
            )
        except Exception:
            pass
        return algo_id
    except Exception as e:
        try:
            write_log(
                actor_user_id=actor_user_id,
                action='ALGORITHM_CREATE',
                target_type='algorithm',
                target_id=None,
                detail=sanitize_detail({
                    'result': 'fail',
                    'request': {
                        'algo_key': algo_key,
                        'name': name,
                        'type': algo_type,
                        'status': status,
                    },
                    'error': str(e),
                    'actor': actor_meta or {},
                }),
            )
        except Exception:
            pass
        raise


def get_algorithm(algo_id: int) -> Optional[Dict]:
    return repo.get_algorithm(algo_id)


def get_algorithm_by_key(algo_key: str) -> Optional[Dict]:
    return repo.get_algorithm_by_key(algo_key)


def update_algorithm(
    algo_id: int,
    name: Optional[str],
    algo_key: Optional[str],
    description: Optional[str],
    algo_type: Optional[str],
    status: Optional[str],
    actor_meta: Optional[Dict[str, Any]] = None,
) -> None:
    before: Optional[Dict] = None
    try:
        before = repo.get_algorithm(algo_id)
    except Exception:
        before = None

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

    try:
        repo.update_algorithm_fields(algo_id, fields)

        after: Optional[Dict] = None
        try:
            after = repo.get_algorithm(algo_id)
        except Exception:
            after = None

        # 仅在 status 变更时记录“启停算法”类审计
        if status is not None:
            try:
                actor_user_id = None
                try:
                    actor_user_id = g.user['id']
                except Exception:
                    actor_user_id = None

                write_log(
                    actor_user_id=actor_user_id,
                    action='ALGORITHM_STATUS_UPDATE',
                    target_type='algorithm',
                    target_id=str(algo_id),
                    detail=sanitize_detail({
                        'result': 'success',
                        'before': {'status': (before or {}).get('status') if isinstance(before, dict) else None},
                        'after': {'status': (after or {}).get('status') if isinstance(after, dict) else status},
                        'extra': {
                            'algo_key': (after or {}).get('algo_key') if isinstance(after, dict) else (before or {}).get('algo_key'),
                            'name': (after or {}).get('name') if isinstance(after, dict) else (before or {}).get('name'),
                        },
                        'actor': actor_meta or {},
                    }),
                )
            except Exception:
                pass

    except Exception as e:
        if status is not None:
            try:
                actor_user_id = None
                try:
                    actor_user_id = g.user['id']
                except Exception:
                    actor_user_id = None

                write_log(
                    actor_user_id=actor_user_id,
                    action='ALGORITHM_STATUS_UPDATE',
                    target_type='algorithm',
                    target_id=str(algo_id),
                    detail=sanitize_detail({
                        'result': 'fail',
                        'before': {'status': (before or {}).get('status') if isinstance(before, dict) else None},
                        'after': {'status': status},
                        'extra': {
                            'algo_key': (before or {}).get('algo_key') if isinstance(before, dict) else None,
                            'name': (before or {}).get('name') if isinstance(before, dict) else None,
                        },
                        'error': str(e),
                        'actor': actor_meta or {},
                    }),
                )
            except Exception:
                pass
        raise


def delete_algorithm(
    algo_id: int,
    actor_meta: Optional[Dict[str, Any]] = None,
) -> None:
    actor_user_id = None
    try:
        actor_user_id = g.user['id']
    except Exception:
        actor_user_id = None

    before: Optional[Dict] = None
    try:
        before = repo.get_algorithm(algo_id)
    except Exception:
        before = None

    try:
        repo.delete_algorithm(algo_id)
        try:
            write_log(
                actor_user_id=actor_user_id,
                action='ALGORITHM_DELETE',
                target_type='algorithm',
                target_id=str(algo_id),
                detail=sanitize_detail({
                    'result': 'success',
                    'before': before or {},
                    'actor': actor_meta or {},
                }),
            )
        except Exception as log_err:
            print('ALGORITHM_DELETE audit log failed(success):', log_err)
    except Exception as e:
        try:
            write_log(
                actor_user_id=actor_user_id,
                action='ALGORITHM_DELETE',
                target_type='algorithm',
                target_id=str(algo_id),
                detail=sanitize_detail({
                    'result': 'fail',
                    'before': before or {},
                    'error': str(e),
                    'actor': actor_meta or {},
                }),
            )
        except Exception as log_err:
            print('ALGORITHM_DELETE audit log failed(fail):', log_err)
        raise


def list_all_algorithms() -> List[Dict]:
    total = repo.count_algorithms()
    if total <= 0:
        return []
    return repo.list_algorithms(offset=0, limit=min(total, 10000))
