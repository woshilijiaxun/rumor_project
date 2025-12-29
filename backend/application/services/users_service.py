from typing import Optional, Dict
from werkzeug.security import generate_password_hash, check_password_hash
from application.repositories.users_repo import (
    list_users as repo_list_users,
    get_user_by_id,
    username_exists,
    update_user_fields,
    get_user_public,
)


def list_users() -> list[Dict]:
    return repo_list_users()


def update_user(
    user_id: int,
    new_username: Optional[str],
    new_email: Optional[str],
    old_password: Optional[str],
    new_password: Optional[str]
) -> Dict:
    """
    返回更新后的用户公开信息（id, username, email, created_at）
    发生校验错误时抛出 ValueError，调用方决定如何转换为 HTTP 响应
    """
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("用户不存在")

    updates: Dict[str, str] = {}

    # 用户名
    if new_username is not None and new_username != user.get('username'):
        if len(new_username) < 3:
            raise ValueError("用户名至少需要3个字符")
        if username_exists(new_username, exclude_user_id=user_id):
            raise ValueError("用户名已存在")
        updates['username'] = new_username

    # 邮箱
    if new_email is not None and new_email != user.get('email'):
        updates['email'] = new_email

    # 密码
    if new_password:
        if len(new_password) < 6:
            raise ValueError("密码至少需要6个字符")
        stored = user.get('password') or ''
        if stored.startswith('pbkdf2:'):
            if not old_password or not check_password_hash(stored, old_password):
                raise ValueError("原密码不正确")
        else:
            if not old_password or stored != old_password:
                raise ValueError("原密码不正确")
        updates['password'] = generate_password_hash(new_password)

    if updates:
        update_user_fields(user_id, updates)

    updated = get_user_public(user_id)
    return updated

