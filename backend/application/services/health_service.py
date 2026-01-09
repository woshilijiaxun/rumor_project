import os
import time
import threading
from datetime import datetime, timezone

_health_cache = {
    'payload': None,
    'lock': threading.Lock(),
}

def _compute_health_payload(app):
    """执行健康检查并返回结果 payload。"""
    with app.app_context():
        from flask import current_app
        from application.common.db import get_db_connection

        t0 = time.time()
        items = []
        overall = 'OK'

        def _worse(a: str, b: str) -> str:
            order = {'OK': 0, 'WARN': 1, 'CRIT': 2, 'UNKNOWN': 3}
            return a if order.get(a, 99) >= order.get(b, 99) else b

        try:
            import psutil
        except ImportError:
            psutil = None

        def _fmt_duration(seconds: int) -> str:
            try:
                seconds = int(seconds)
            except (ValueError, TypeError):
                return ''
            if seconds < 0:
                seconds = 0
            days, rem = divmod(seconds, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, secs = divmod(rem, 60)
            if days > 0:
                return f"{days}天{hours:02d}小时{minutes:02d}分"
            if hours > 0:
                return f"{hours}小时{minutes:02d}分{secs:02d}秒"
            if minutes > 0:
                return f"{minutes}分{secs:02d}秒"
            return f"{secs}秒"

        # 1) 应用信息
        app_check_t0 = time.time()
        app_metrics = {}
        try:
            import sys
            import flask
            app_metrics.update({
                'pid': os.getpid(),
                'server_time': datetime.now(timezone.utc).isoformat(),
                'python_version': sys.version.split(' ')[0],
                'flask_version': getattr(flask, '__version__', None),
                'debug': bool(current_app.config.get('DEBUG', False)),
            })
            if psutil:
                p = psutil.Process(os.getpid())
                uptime_seconds = int(time.time() - p.create_time())
                app_metrics['uptime_seconds'] = uptime_seconds
                app_metrics['uptime_human'] = _fmt_duration(uptime_seconds)
                app_metrics['memory_rss_mb'] = round(p.memory_info().rss / 1024**2, 2)
                app_metrics['num_threads'] = p.num_threads()
        except Exception:
            pass
        app_metrics['check_ms'] = int((time.time() - app_check_t0) * 1000)
        items.append({
            'key': 'app',
            'name': '应用服务',
            'status': 'OK',
            'message': '服务运行正常（单进程）',
            'metrics': app_metrics,
        })

        # 2) MySQL
        db_check_t0 = time.time()
        mysql_item = {
            'key': 'mysql',
            'name': 'MySQL 数据库',
            'status': 'OK',
            'message': '',
            'metrics': {},
        }
        conn, cur = None, None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            t_latency = time.time()
            cur.execute('SELECT 1')
            cur.fetchone()
            mysql_item['metrics']['latency_ms'] = int((time.time() - t_latency) * 1000)

            cur.execute("SHOW STATUS LIKE 'Threads_connected'")
            mysql_item['metrics']['threads_connected'] = int(cur.fetchone()[1])
            cur.execute("SHOW STATUS LIKE 'Threads_running'")
            mysql_item['metrics']['threads_running'] = int(cur.fetchone()[1])

            if mysql_item['metrics']['latency_ms'] > 200:
                mysql_item['status'] = 'WARN'
                mysql_item['message'] = f"连接正常，但延迟偏高：{mysql_item['metrics']['latency_ms']}ms"
            else:
                mysql_item['message'] = f"连接正常：{mysql_item['metrics']['latency_ms']}ms"
            overall = _worse(overall, mysql_item['status'])
        except Exception as e:
            mysql_item['status'] = 'CRIT'
            mysql_item['message'] = f'数据库连接失败: {str(e)}'
            overall = _worse(overall, mysql_item['status'])
        finally:
            if cur: cur.close()
            if conn: conn.close()
        mysql_item['metrics']['check_ms'] = int((time.time() - db_check_t0) * 1000)
        items.append(mysql_item)

        # 3) 磁盘空间
        disk_check_t0 = time.time()
        disk_item = {
            'key': 'disk',
            'name': '磁盘空间 (上传目录)',
            'status': 'OK',
            'message': '',
            'metrics': {},
        }
        try:
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            if upload_folder and os.path.exists(upload_folder) and psutil:
                usage = psutil.disk_usage(upload_folder)
                percent = float(usage.percent)
                disk_item['metrics'] = {
                    'path': upload_folder,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'percent_used': percent,
                }
                if percent > 95:
                    disk_item['status'] = 'CRIT'
                    disk_item['message'] = f'磁盘空间严重不足 (已用 {percent}%)'
                elif percent > 80:
                    disk_item['status'] = 'WARN'
                    disk_item['message'] = f'磁盘空间警告 (已用 {percent}%)'
                else:
                    disk_item['message'] = f'磁盘空间正常 (已用 {percent}%)'
            else:
                disk_item['status'] = 'UNKNOWN'
                disk_item['message'] = '无法获取上传目录或 psutil 不可用'
            overall = _worse(overall, disk_item['status'])
        except Exception as e:
            disk_item['status'] = 'CRIT'
            disk_item['message'] = f'检查磁盘空间失败: {str(e)}'
            overall = _worse(overall, disk_item['status'])
        disk_item['metrics']['check_ms'] = int((time.time() - disk_check_t0) * 1000)
        items.append(disk_item)

        return {
            'overall': overall,
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'duration_ms': int((time.time() - t0) * 1000),
            'items': items,
        }

def run_health_check_job(app):
    """后台线程执行的函数。"""
    try:
        app.logger.info('Health check: running initial check...')
    except Exception:
        pass

    payload = _compute_health_payload(app)
    with _health_cache['lock']:
        _health_cache['payload'] = payload

    try:
        app.logger.info('Health check: initial check completed at %s', payload.get('checked_at'))
    except Exception:
        pass

    while True:
        time.sleep(600)  # 10分钟
        try:
            app.logger.info('Health check: running scheduled check...')
        except Exception:
            pass

        payload = _compute_health_payload(app)
        with _health_cache['lock']:
            _health_cache['payload'] = payload

        try:
            app.logger.info('Health check: scheduled check completed at %s', payload.get('checked_at'))
        except Exception:
            pass


def start_health_daemon(app):
    """启动健康检查后台守护线程。"""
    thread = threading.Thread(target=run_health_check_job, args=(app,), daemon=True)
    thread.start()
    try:
        app.logger.info('Health check daemon started (every 10 minutes).')
    except Exception:
        pass

def get_last_health_report():
    """获取最后一次缓存的健康检查报告。"""
    with _health_cache['lock']:
        return _health_cache['payload']

def force_refresh_health_check(app):
    """强制执行一次健康检查并更新缓存。"""
    payload = _compute_health_payload(app)
    with _health_cache['lock']:
        _health_cache['payload'] = payload
    return payload

