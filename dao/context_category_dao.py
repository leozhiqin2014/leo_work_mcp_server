"""
上下文分类 DAO
封装 context_category 表的数据库操作。
"""

import logging
from typing import Any

from dao.db import get_connection, get_dict_cursor

logger = logging.getLogger(__name__)


def list_all() -> list[dict[str, Any]]:
    """查询所有正常状态的分类记录，按 level_one/level_two/level_three/level_four 排序"""
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """
            SELECT id, level_one, level_two, level_three, level_four,
                   description, sort_order, status
            FROM context_category
            WHERE status = 1
            ORDER BY level_one, level_two, level_three, level_four, sort_order
            """
        )
        return list(cursor.fetchall())
    finally:
        conn.close()


def exists(
    level_one: str,
    level_two: str,
    level_three: str = "",
    level_four: str = "",
) -> bool:
    """检查 level_one + level_two 是否存在于维度表（status=1）"""
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """
            SELECT id FROM context_category
            WHERE level_one = %s AND level_two = %s
              AND status = 1
            LIMIT 1
            """,
            (level_one, level_two),
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def ensure_exists(
    level_one: str,
    level_two: str,
    level_three: str = "",
    level_four: str = "",
) -> int:
    """确保分类记录存在，不存在则自动创建。返回记录 ID。"""
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """
            SELECT id FROM context_category
            WHERE level_one = %s AND level_two = %s
              AND level_three = %s AND level_four = %s
            LIMIT 1
            """,
            (level_one, level_two, level_three, level_four),
        )
        row = cursor.fetchone()
        if row:
            return row["id"]

        cursor.execute(
            """
            INSERT INTO context_category (level_one, level_two, level_three, level_four)
            VALUES (%s, %s, %s, %s)
            """,
            (level_one, level_two, level_three, level_four),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
