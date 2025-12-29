"""
数据库初始化脚本
用于创建数据库和表结构
"""
import mysql.connector
from mysql.connector import errorcode
from werkzeug.security import generate_password_hash

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'ljx123456',
    'charset': 'utf8mb4'
}

DATABASE_NAME = 'new_db'

def create_database():
    """创建数据库"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ 数据库 {DATABASE_NAME} 创建成功或已存在")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False


def create_tables():
    """创建数据表"""
    try:
        config = DB_CONFIG.copy()
        config['database'] = DATABASE_NAME
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)

        # 创建用户表
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_username (username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_users_table)
        print("✓ 用户表创建成功或已存在")

        # 创建上传文件表
        create_uploads_table = """
        CREATE TABLE IF NOT EXISTS uploads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            original_name VARCHAR(255) NOT NULL,
            stored_name VARCHAR(255) NOT NULL,
            mime_type VARCHAR(100),
            size_bytes BIGINT,
            storage_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            CONSTRAINT fk_uploads_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_uploads_table)
        print("✓ 上传文件表创建成功或已存在")

        # 创建算法表
        create_algorithms_table = """
        CREATE TABLE IF NOT EXISTS algorithms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            name VARCHAR(255) NOT NULL,
            algo_key VARCHAR(64) NOT NULL,
            description TEXT,
            type VARCHAR(100),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY ux_algorithms_algo_key (algo_key),
            INDEX idx_user_id (user_id),
            INDEX idx_status (status),
            CONSTRAINT fk_algorithms_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_algorithms_table)
        print("✓ 算法表创建成功或已存在")

        # 插入测试用户（如果不存在）
        check_user = "SELECT COUNT(*) as count FROM users WHERE username = 'admin'"
        cursor.execute(check_user)
        result = cursor.fetchone()

        if result['count'] == 0:
            # 使用哈希密码存储测试账号
            pwd_hash = generate_password_hash('admin123')
            insert_test_user = """
            INSERT INTO users (username, password, email) 
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_test_user, ('admin', pwd_hash, 'admin@example.com'))
            conn.commit()
            print("✓ 测试用户创建成功 (用户名: admin, 密码: admin123，已使用哈希存储)")
        else:
            print("✓ 测试用户已存在")

        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("✗ 数据库登录失败，请检查用户名/密码")
        else:
            print(f"✗ 创建表失败: {err}")
        return False
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("开始初始化数据库...")
    print("=" * 50)

    if create_database():
        if create_tables():
            print("=" * 50)
            print("数据库初始化完成！")
            print("=" * 50)
            print("\n测试账号信息:")
            print("  用户名: admin")
            print("  密码: admin123")
            print("=" * 50)
        else:
            print("数据库初始化失败！")
    else:
        print("数据库初始化失败！")


if __name__ == '__main__':
    main()
