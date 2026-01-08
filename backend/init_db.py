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
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_role (role)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_users_table)
        print("✓ 用户表创建成功或已存在")

        # 创建上传文件表
        create_uploads_table = """
        CREATE TABLE IF NOT EXISTS uploads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            visibility VARCHAR(20) NOT NULL DEFAULT 'private',
            original_name VARCHAR(255) NOT NULL,
            stored_name VARCHAR(255) NOT NULL,
            mime_type VARCHAR(100),
            size_bytes BIGINT,
            storage_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_visibility (visibility),
            INDEX idx_visibility_user_id (visibility, user_id),
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

        # 创建识别任务表（历史）
        create_identification_tasks_table = """
        CREATE TABLE IF NOT EXISTS identification_tasks (
            task_id VARCHAR(64) PRIMARY KEY,
            user_id INT NOT NULL,
            file_id INT NOT NULL,
            algorithm_key VARCHAR(64) NOT NULL,
            params JSON NULL,
            status VARCHAR(20) NOT NULL,
            progress INT DEFAULT 0,
            stage VARCHAR(50) DEFAULT '',
            message VARCHAR(255) DEFAULT '',
            error JSON NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP NULL,
            ended_at TIMESTAMP NULL,
            INDEX idx_user_created_at (user_id, created_at),
            INDEX idx_file_id (file_id),
            INDEX idx_status (status),
            CONSTRAINT fk_ident_tasks_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            CONSTRAINT fk_ident_tasks_file FOREIGN KEY (file_id) REFERENCES uploads(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_identification_tasks_table)
        print("✓ 识别任务表创建成功或已存在")

                # 在 create_tables() 函数中，添加以下代码（可以放在其他表创建语句后面）：
        create_audit_logs_table = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            actor_user_id INT NULL,
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(100) NOT NULL,
            target_id VARCHAR(100) NULL,
            detail_json TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_actor_user_id (actor_user_id),
            INDEX idx_action (action),
            INDEX idx_target (target_type, target_id),
            INDEX idx_created_at (created_at),
            CONSTRAINT fk_audit_logs_user FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_audit_logs_table)
        print("✓ 审计日志表创建成功或已存在")

        
        # 创建识别结果表
        create_identification_results_table = """
        CREATE TABLE IF NOT EXISTS identification_task_results (
            task_id VARCHAR(64) PRIMARY KEY,
            result JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_ident_results_task FOREIGN KEY (task_id) REFERENCES identification_tasks(task_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_identification_results_table)
        print("✓ 识别任务结果表创建成功或已存在")

        # 创建文件拓扑缓存表（拓扑只由文件决定）
        create_file_graph_cache_table = """
        CREATE TABLE IF NOT EXISTS file_graph_cache (
            file_id INT PRIMARY KEY,
            graph_json JSON NOT NULL,
            meta_json JSON NULL,
            graph_version VARCHAR(32) NOT NULL DEFAULT 'v1',
            max_edges INT NOT NULL DEFAULT 10000,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_graph_cache_file FOREIGN KEY (file_id) REFERENCES uploads(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_file_graph_cache_table)
        print("✓ 文件拓扑缓存表创建成功或已存在")

        # 创建系统配置表（system_config）
        create_system_config_table = """
        CREATE TABLE IF NOT EXISTS system_config (
            `key` VARCHAR(64) PRIMARY KEY,
            `value` TEXT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            updated_by INT NULL,
            INDEX idx_updated_by (updated_by)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_system_config_table)
        print("✓ 系统配置表创建成功或已存在")

        # 插入测试用户（如果不存在）
        check_user = "SELECT COUNT(*) as count FROM users WHERE username = 'admin'"
        cursor.execute(check_user)
        result = cursor.fetchone()

        if result['count'] == 0:
            # 使用哈希密码存储测试账号
            pwd_hash = generate_password_hash('admin123')
            cursor.execute("INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)", ('admin', pwd_hash, 'admin@example.com', 'admin'))
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
