"""
配置文件
"""
import os

class Config:
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = 'ljx123456'
    DB_NAME = 'new_db'
    DB_CHARSET = 'utf8mb4'
    ...
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

