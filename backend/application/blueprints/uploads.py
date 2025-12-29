import os
import uuid
from flask import Blueprint, request, g, current_app, send_from_directory
from werkzeug.utils import secure_filename
from mysql.connector import Error

from application.common.auth import require_auth
from application.common.responses import ok, fail
from application.services import uploads_service

bp = Blueprint('uploads', __name__)

ALLOWED_EXTENSIONS = set(['txt', 'csv'])


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/upload', methods=['POST'])
@require_auth
def upload_file():
    try:
        if 'file' not in request.files:
            return fail("未找到文件字段(file)", http_code=400)
        f = request.files['file']
        if f.filename == '':
            return fail("未选择文件", http_code=400)

        filename = secure_filename(f.filename)
        if not allowed_file(filename):
            return fail("不支持的文件类型", http_code=400)

        ext = filename.rsplit('.', 1)[1].lower()
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
        rel_path = os.path.join('uploads', stored_name)
        f.save(abs_path)
        size_bytes = os.path.getsize(abs_path)
        mime_type = f.mimetype or ''

        # 通过 service 写数据库记录
        upload_id = uploads_service.create_upload_record(
            user_id=g.user['id'],
            original_name=filename,
            stored_name=stored_name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=rel_path
        )

        return ok({
            "id": upload_id,
            "original_name": filename,
            "stored_name": stored_name,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "storage_path": rel_path
        }, message="上传成功")
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/uploads', methods=['GET'])
@require_auth
def list_uploads():
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        payload = uploads_service.list_uploads_paginated(page=page, page_size=page_size)
        return ok(payload)
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/uploads/<int:file_id>/download', methods=['GET'])
@require_auth
def download_upload(file_id: int):
    try:
        row = uploads_service.get_upload_record(file_id)
        if not row:
            return fail("文件不存在", http_code=404)
        stored_name = row['stored_name']
        original_name = row['original_name']
        directory = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(directory=directory, path=stored_name, as_attachment=True, download_name=original_name)
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/uploads/<int:file_id>/file', methods=['GET'])
@require_auth
def inline_file(file_id: int):
    try:
        row = uploads_service.get_upload_record(file_id)
        if not row:
            return fail("文件不存在", http_code=404)
        directory = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(directory=directory, path=row['stored_name'], as_attachment=False)
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")


@bp.route('/uploads/<int:file_id>', methods=['DELETE'])
@require_auth
def delete_upload(file_id: int):
    try:
        row = uploads_service.get_upload_record(file_id)
        if not row:
            return fail("文件不存在", http_code=404)

        # 先删物理文件
        try:
            abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], row['stored_name'])
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except Exception:
            pass

        # 再删记录
        uploads_service.delete_upload_record(file_id)
        return ok(message="删除成功")
    except Error as e:
        return fail("数据库错误: " + str(e), http_code=500, status="error")
    except Exception as e:
        return fail("系统错误: " + str(e), http_code=500, status="error")
