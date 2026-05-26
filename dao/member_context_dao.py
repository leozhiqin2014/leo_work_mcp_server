"""
成员上下文记录 DAO
封装 member_context 表的所有数据库操作。
"""

import logging
from typing import Any, Optional

from dao.db import get_connection, get_dict_cursor
from models.member_context import ContentFormat, ContextStatus, ContextPermission

logger = logging.getLogger(__name__)


def get_latest_member_name(member_nickname: str) -> Optional[str]:
    """按昵称查询最新的 member_name（用于新增时自动填充）

    Args:
        member_nickname: 成员昵称

    Returns:
        成员名称字符串，未找到时返回 None
    """
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """
            SELECT member_name
            FROM member_context
            WHERE member_nickname = %s
              AND status = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (member_nickname, int(ContextStatus.NORMAL)),
        )
        row = cursor.fetchone()
        return row["member_name"] if row and row.get("member_name") else None
    finally:
        conn.close()


def insert_context(
    member_nickname: str,
    member_name: str,
    context_type_level_one: str,
    context_type_level_two: str,
    context_type_level_three: str,
    context_type_level_four: str,
    content_format: ContentFormat,
    content: Optional[str],
    cos_url: Optional[str],
    cos_key: Optional[str],
    file_name: Optional[str],
    file_size: int,
    status: ContextStatus,
    permission: ContextPermission,
    remark: str,
    tags: str = "",
) -> int:
    """插入一条上下文记录

    Returns:
        新插入记录的自增 ID
    """
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        sql = """
            INSERT INTO member_context (
                member_nickname,
                member_name,
                context_type_level_one,
                context_type_level_two,
                context_type_level_three,
                context_type_level_four,
                content_format,
                content,
                cos_url,
                cos_key,
                file_name,
                file_size,
                status,
                permission,
                remark,
                tags
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """
        params = [
            member_nickname,
            member_name,
            context_type_level_one,
            context_type_level_two,
            context_type_level_three,
            context_type_level_four,
            int(content_format),
            content,
            cos_url,
            cos_key,
            file_name,
            file_size,
            int(status),
            int(permission),
            remark,
            tags,
        ]
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_context(context_id: int, fields: dict[str, Any]) -> bool:
    """按主键更新上下文记录，仅更新 fields 中不为 None 的字段

    Args:
        context_id: 记录 ID
        fields: 待更新字段字典，值为 None 的字段跳过

    Returns:
        是否更新成功（影响行数 > 0）
    """
    updates = {k: v for k, v in fields.items() if v is not None}
    if not updates:
        return False

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    params = list(updates.values()) + [context_id]

    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            f"UPDATE member_context SET {set_clause} WHERE id = %s",
            params,
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_context_by_id(context_id: int) -> dict[str, Any] | None:
    """按主键查询单条上下文记录

    Args:
        context_id: 记录 ID

    Returns:
        记录字典，未找到时返回 None
    """
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """
            SELECT *
            FROM member_context
            WHERE id = %s
              AND status = %s
            """,
            (context_id, int(ContextStatus.NORMAL)),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def query_contexts(
    member_nickname: str | None = None,
    member_name: str | None = None,
    context_type_level_one: str | None = None,
    context_type_level_two: str | None = None,
    context_type_level_three: str | None = None,
    context_type_level_four: str | None = None,
    content_format: ContentFormat | None = None,
    status: ContextStatus = ContextStatus.NORMAL,
    start_time: str | None = None,
    end_time: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """按昵称/名称及多维度条件查询上下文记录列表（分页）

    Args:
        member_nickname: 成员昵称（与 member_name 至少传一个）
        member_name: 成员名称（与 member_nickname 至少传一个）
        context_type_level_one: 1级分类过滤（必填）
        context_type_level_two: 2级分类过滤（必填）
        context_type_level_three: 3级分类过滤（必填）
        context_type_level_four: 4级分类过滤（可选）
        content_format: 内容格式过滤，ContentFormat 枚举（可选）
        status: 记录状态过滤，默认仅返回正常状态
        start_time: 创建时间下限，格式 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS（可选）
        end_time: 创建时间上限，格式 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS（可选）
        keyword: 关键词模糊匹配，命中 level_four/remark/tags 任一即返回（可选）
        page: 页码，从 1 开始（默认 1）
        page_size: 每页条数（默认 20，最大 100）

    Returns:
        包含 total、page、page_size、records 的字典

    Raises:
        ValueError: 未传入 1/2/3 级分类
    """
    if not context_type_level_one or not context_type_level_two or not context_type_level_three:
        raise ValueError("查询必须同时指定 context_type_level_one、context_type_level_two、context_type_level_three")

    page_size = min(page_size, 100)
    offset = (max(page, 1) - 1) * page_size

    conditions = ["status = %s"]
    params: list[Any] = [int(status)]

    if member_nickname:
        conditions.append("member_nickname = %s")
        params.append(member_nickname)
    if member_name:
        conditions.append("member_name = %s")
        params.append(member_name)

    if context_type_level_one:
        conditions.append("context_type_level_one = %s")
        params.append(context_type_level_one)
    if context_type_level_two:
        conditions.append("context_type_level_two = %s")
        params.append(context_type_level_two)
    if context_type_level_three:
        conditions.append("context_type_level_three = %s")
        params.append(context_type_level_three)
    if context_type_level_four:
        conditions.append("context_type_level_four = %s")
        params.append(context_type_level_four)
    if content_format is not None:
        conditions.append("content_format = %s")
        params.append(int(content_format))
    if start_time:
        conditions.append("created_at >= %s")
        params.append(start_time)
    if end_time:
        conditions.append("created_at <= %s")
        params.append(end_time)
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(
            "(context_type_level_four LIKE %s"
            + " OR remark LIKE %s"
            + " OR tags LIKE %s)"
        )
        params.extend([kw, kw, kw])

    where_clause = " AND ".join(conditions)

    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)

        # 查询总数
        cursor.execute(
            f"SELECT COUNT(*) AS total FROM member_context WHERE {where_clause}",
            params,
        )
        count_row = cursor.fetchone()
        total = count_row["total"] if count_row else 0

        # 查询分页数据
        cursor.execute(
            f"""
            SELECT
                id, member_nickname, member_name,
                context_type_level_one, context_type_level_two,
                context_type_level_three, context_type_level_four,
                content_format, content,
                cos_url, cos_key, file_name, file_size,
                status, permission, remark, tags,
                created_at, updated_at
            FROM member_context
            WHERE {where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, offset],
        )
        records = list(cursor.fetchall())

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "records": records,
        }
    finally:
        conn.close()


def get_context_type_summary(member_nickname: str) -> list[dict[str, Any]]:
    """查询某成员所有不重复的四级分类组合及每组记录数

    Returns:
        按分类路径排序的列表，每项包含四级分类字段和 count
    """
    conn = get_connection()
    try:
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """
            SELECT
                context_type_level_one,
                context_type_level_two,
                context_type_level_three,
                context_type_level_four,
                COUNT(*) AS count
            FROM member_context
            WHERE member_nickname = %s AND status = 1
            GROUP BY
                context_type_level_one,
                context_type_level_two,
                context_type_level_three,
                context_type_level_four
            ORDER BY
                context_type_level_one,
                context_type_level_two,
                context_type_level_three,
                context_type_level_four
            """,
            (member_nickname,),
        )
        return list(cursor.fetchall())
    finally:
        conn.close()

