import mysql.connector
from mysql.connector import Error, pooling
from config import Config

_pool = None


def init_db_pool():
    global _pool
    if _pool is not None:
        return _pool
    _pool = pooling.MySQLConnectionPool(
        pool_name="app_pool",
        pool_size=5,
        pool_reset_session=True,
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset=Config.DB_CHARSET,
        time_zone='+8:00'
    )
    return _pool


def get_db_connection():
    """
    获取数据库连接：优先使用连接池；如池未初始化则回退直连。
    调用方负责关闭连接（conn.close()）。
    """
    global _pool
    try:
        if _pool is None:
            # 延迟初始化，避免导入顺序问题
            try:
                init_db_pool()
            except Exception:
                # 回退为单连接（不推荐，仅作为兜底）
                return mysql.connector.connect(
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    charset=Config.DB_CHARSET,
                    time_zone='+8:00'
                )
        return _pool.get_connection()
    except Exception as e:
        print(f"数据库连接失败: {e}")
        raise
