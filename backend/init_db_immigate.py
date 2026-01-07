
import mysql.connector
from mysql.connector import Error
from init_db import DB_CONFIG, DATABASE_NAME

cfg = DB_CONFIG.copy()
cfg['database'] = DATABASE_NAME

def column_exists(cur, table, col):
    cur.execute("""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
    """, (DATABASE_NAME, table, col))
    return cur.fetchone()[0] > 0

try:
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()

    # users.role
    if not column_exists(cur, 'users', 'role'):
        cur.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
        conn.commit()
        print('✓ users.role 已添加')
    else:
        print('✓ users.role 已存在，跳过')

    # users.idx_role
    cur.execute("SHOW INDEX FROM users WHERE Key_name='idx_role'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_role ON users(role)")
        conn.commit()
        print('✓ users.idx_role 已创建')
    else:
        print('✓ users.idx_role 已存在，跳过')

    # ensure admin user role
    cur.execute("UPDATE users SET role='admin' WHERE username='admin'")
    conn.commit()
    print("✓ admin 用户 role 已设置为 admin（如果存在）")

    # uploads.visibility
    if not column_exists(cur, 'uploads', 'visibility'):
        cur.execute("ALTER TABLE uploads ADD COLUMN visibility VARCHAR(20) NOT NULL DEFAULT 'private'")
        conn.commit()
        print('✓ uploads.visibility 已添加')
    else:
        print('✓ uploads.visibility 已存在，跳过')

    # uploads.idx_visibility
    cur.execute("SHOW INDEX FROM uploads WHERE Key_name='idx_visibility'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_visibility ON uploads(visibility)")
        conn.commit()
        print('✓ uploads.idx_visibility 已创建')
    else:
        print('✓ uploads.idx_visibility 已存在，跳过')

    # uploads.idx_visibility_user_id
    cur.execute("SHOW INDEX FROM uploads WHERE Key_name='idx_visibility_user_id'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_visibility_user_id ON uploads(visibility, user_id)")
        conn.commit()
        print('✓ uploads.idx_visibility_user_id 已创建')
    else:
        print('✓ uploads.idx_visibility_user_id 已存在，跳过')

    cur.close()
    conn.close()
    print("=== 迁移完成 ===")

except Error as e:
    print("✗ 迁移失败：", e)
    raise
