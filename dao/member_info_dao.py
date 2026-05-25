"""
成员信息 DAO
封装 member_info 表的数据库操作。
"""

import logging
from typing import Any

from dao.db import get_connection, get_dict_cursor

logger = logging.getLogger(__name__)


def list_member_nicknames() -> list[str]:
    """查询所有正常状态成员的昵称列表

    Returns:
        member_nickname 字符串列表
    """
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """
            SELECT member_nickname
            FROM member_info
            WHERE status = 1
            ORDER BY id ASC
            """
        )
        rows = cursor.fetchall()
        return [row["member_nickname"] for row in rows]
    finally:
        conn.close()
