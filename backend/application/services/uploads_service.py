from typing import Dict, Optional, Any

from application.common.auth import is_admin
from application.repositories.uploads_repo import (
    create_upload as repo_create_upload,
    count_uploads as repo_count_uploads,
    list_uploads as repo_list_uploads,
    get_upload_by_id as repo_get_upload_by_id,
    delete_upload as repo_delete_upload,
)
from application.services.audit_logs_service import write_log
from application.services.audit_context import sanitize_detail


def create_upload_record(
    user_id: int,
    original_name: str,
    stored_name: str,
    mime_type: str,
    size_bytes: int,
    storage_path: str,
    visibility: str = 'private',
    actor_meta: Optional[Dict[str, Any]] = None,
) -> int:
    """创建上传记录，并写审计日志（关键操作）。

    actor_meta 可包含：ip、user_agent 等。
    """
    try:
        upload_id = repo_create_upload(user_id, original_name, stored_name, mime_type, size_bytes, storage_path, visibility)
        try:
            write_log(
                actor_user_id=user_id,
                action='FILE_UPLOAD',
                target_type='upload',
                target_id=str(upload_id),
                detail=sanitize_detail({
                    'result': 'success',
                    'request': {'visibility': visibility},
                    'extra': {
                        'original_name': original_name,
                        'stored_name': stored_name,
                        'mime_type': mime_type,
                        'size_bytes': size_bytes,
                        'storage_path': storage_path,
                    },
                    'actor': actor_meta or {},
                }),
            )
        except Exception:
            pass
        return upload_id
    except Exception as e:
        try:
            write_log(
                actor_user_id=user_id,
                action='FILE_UPLOAD',
                target_type='upload',
                target_id=None,
                detail=sanitize_detail({
                    'result': 'fail',
                    'request': {'visibility': visibility},
                    'extra': {
                        'original_name': original_name,
                        'mime_type': mime_type,
                        'size_bytes': size_bytes,
                    },
                    'error': str(e),
                    'actor': actor_meta or {},
                }),
            )
        except Exception:
            pass
        raise


def list_uploads_paginated(page: int, page_size: int, current_user_id: int) -> Dict:
    """普通用户：public + 自己的 private；管理员：全量。"""
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 10), 1), 100)
    offset = (page - 1) * page_size

    if is_admin():
        where_sql = ""
        params: tuple = ()
    else:
        where_sql = "(visibility='public' OR user_id=%s)"
        params = (int(current_user_id),)

    total = repo_count_uploads(where_sql=where_sql, params=params)
    items = repo_list_uploads(offset=offset, limit=page_size, where_sql=where_sql, params=params)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_upload_record(file_id: int) -> Optional[Dict]:
    return repo_get_upload_by_id(file_id)


def delete_upload_record(
    file_id: int,
    actor_user_id: Optional[int] = None,
    actor_meta: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """删除上传记录，并写审计日志（关键操作）。

    context 建议包含：by_admin、original_name、stored_name 等（由调用方在删除前读取记录并传入）。
    """
    ctx = context or {}
    try:
        repo_delete_upload(file_id)
        try:
            write_log(
                actor_user_id=actor_user_id,
                action='FILE_DELETE',
                target_type='upload',
                target_id=str(file_id),
                detail=sanitize_detail({
                    'result': 'success',
                    'extra': {
                        **ctx,
                        'file_id': file_id,
                    },
                    'actor': actor_meta or {},
                }),
            )
        except Exception:
            pass
    except Exception as e:
        try:
            write_log(
                actor_user_id=actor_user_id,
                action='FILE_DELETE',
                target_type='upload',
                target_id=str(file_id),
                detail=sanitize_detail({
                    'result': 'fail',
                    'extra': {
                        **ctx,
                        'file_id': file_id,
                    },
                    'error': str(e),
                    'actor': actor_meta or {},
                }),
            )
        except Exception:
            pass
        raise

