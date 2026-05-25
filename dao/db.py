"""
数据库连接配置
所有 DAO 模块通过此模块获取连接，避免重复配置。
"""

import os

import pymysql
import pymysql.cursors

# 数据库连接配置必须通过环境变量注入；host/password 不提供默认值以避免误连真实环境
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "work_data"),
    "charset": "utf8mb4",
}


def get_connection() -> pymysql.connections.Connection:
    """创建并返回一个新的数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def get_dict_cursor(conn: pymysql.connections.Connection) -> pymysql.cursors.DictCursor:
    """在指定连接上创建 DictCursor"""
    return conn.cursor(pymysql.cursors.DictCursor)
