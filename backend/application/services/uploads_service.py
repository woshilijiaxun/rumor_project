from typing import Dict, List, Optional, Tuple
from application.repositories.uploads_repo import (
    create_upload as repo_create_upload,
    count_uploads as repo_count_uploads,
    list_uploads as repo_list_uploads,
    get_upload_by_id as repo_get_upload_by_id,
    delete_upload as repo_delete_upload,
)


def create_upload_record(user_id: int, original_name: str, stored_name: str, mime_type: str, size_bytes: int, storage_path: str) -> int:
    return repo_create_upload(user_id, original_name, stored_name, mime_type, size_bytes, storage_path)


def list_uploads_paginated(page: int, page_size: int) -> Dict:
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 10), 1), 100)
    offset = (page - 1) * page_size
    total = repo_count_uploads()
    items = repo_list_uploads(offset=offset, limit=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_upload_record(file_id: int) -> Optional[Dict]:
    return repo_get_upload_by_id(file_id)


def delete_upload_record(file_id: int) -> None:
    repo_delete_upload(file_id)

