"""
标签 DAO
封装 tag 标签字典表的数据库操作。
标签与上下文的关联直接存储在 member_context.tags 字段（逗号分隔字符串）。
"""

import logging
from typing import Any

from dao.db import get_connection, get_dict_cursor

logger = logging.getLogger(__name__)


def list_all() -> list[dict[str, Any]]:
    """查询所有正常状态的标签"""
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            "SELECT id, name, color, description FROM tag WHERE status = 1 ORDER BY id"
        )
        return list(cursor.fetchall())
    finally:
        conn.close()


def ensure_tags_exist(tag_names: list[str]) -> None:
    """确保标签名称都存在于字典表，不存在则自动创建"""
    if not tag_names:
        return
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            cursor.execute(
                "INSERT IGNORE INTO tag (name) VALUES (%s)",
                (name,),
            )
        conn.commit()
    finally:
        conn.close()
