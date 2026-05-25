"""
健康记录 DAO
封装 family_health_record 表的所有数据库操作。
"""

import logging
from typing import Any

from dao.db import get_connection, get_dict_cursor

logger = logging.getLogger(__name__)


def get_latest_record_by_nickname(member_nickname: str) -> dict[str, Any] | None:
    """按昵称查询最新的一条健康记录（用于获取 member_name 和 height）

    Args:
        member_nickname: 成员昵称

    Returns:
        包含 member_name、height 字段的字典，未找到时返回 None
    """
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """
            SELECT member_name, height
            FROM family_health_record
            WHERE member_nickname = %s
            ORDER BY record_date DESC, id DESC
            LIMIT 1
            """,
            (member_nickname,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def query_records(
    member_nickname: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    """查询指定昵称的健康记录列表

    Args:
        member_nickname: 成员昵称
        start_date: 开始日期，格式 YYYY-MM-DD（可选）
        end_date: 结束日期，格式 YYYY-MM-DD（可选）

    Returns:
        健康记录字典列表，按 record_date 降序排列
    """
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)

        sql = """
            SELECT
                id,
                member_name,
                member_nickname,
                record_date,
                height,
                weight,
                bmi,
                body_fat_rate,
                created_at
            FROM family_health_record
            WHERE member_nickname = %s
        """
        params: list[Any] = [member_nickname]

        if start_date:
            sql += " AND record_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND record_date <= %s"
            params.append(end_date)

        sql += " ORDER BY record_date DESC"

        cursor.execute(sql, params)
        return list(cursor.fetchall())
    finally:
        conn.close()


def insert_record(
    member_name: str,
    member_nickname: str,
    record_date: str,
    height: float,
    weight: float,
    bmi: float,
    body_fat_rate: float,
) -> int:
    """插入一条健康记录

    Args:
        member_name: 成员名称
        member_nickname: 成员昵称
        record_date: 记录日期，格式 YYYY-MM-DD
        height: 身高（cm）
        weight: 体重（kg）
        bmi: BMI 指数
        body_fat_rate: 体脂率

    Returns:
        新插入记录的自增 ID
    """
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        sql = """
            INSERT INTO family_health_record
                (member_name, member_nickname, record_date, height, weight, bmi, body_fat_rate, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = [member_name, member_nickname, record_date, height, weight, bmi, body_fat_rate]
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
