from typing import Dict, Optional
from application.common.auth import is_admin
from application.repositories.uploads_repo import (
    create_upload as repo_create_upload,
    count_uploads as repo_count_uploads,
    list_uploads as repo_list_uploads,
    get_upload_by_id as repo_get_upload_by_id,
    delete_upload as repo_delete_upload,
)


def create_upload_record(user_id: int, original_name: str, stored_name: str, mime_type: str, size_bytes: int, storage_path: str, visibility: str = 'private') -> int:
    return repo_create_upload(user_id, original_name, stored_name, mime_type, size_bytes, storage_path, visibility)


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


def delete_upload_record(file_id: int) -> None:
    repo_delete_upload(file_id)

