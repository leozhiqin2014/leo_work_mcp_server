"""
家庭成员上下文记录工具模块
"""

import logging
from typing import Optional

from dao import member_context_dao
from dao import member_info_dao
from dao import context_category_dao
from dao import tag_dao
from models.member_context import ContentFormat, ContextStatus, ContextPermission
from utils.cos_helper import get_presigned_url
from utils import vector_index

logger = logging.getLogger(__name__)


def register_tools(mcp) -> None:
    """注册成员上下文相关工具"""

    @mcp.tool()
    def save_member_context(
        member_nickname: str,
        context_type_level_one: str,
        context_type_level_two: str,
        content: Optional[str] = None,
        record_id: Optional[int] = None,
        member_name: Optional[str] = None,
        context_type_level_three: Optional[str] = None,
        context_type_level_four: Optional[str] = None,
        cos_url: Optional[str] = None,
        cos_key: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        permission: int = ContextPermission.PRIVATE,
        remark: Optional[str] = None,
        tags: Optional[str] = None,
    ):
        """存储或更新家庭成员上下文信息

        传入 record_id 时执行更新（仅更新非空字段），否则新增记录。
        纯文字内容时只需传 content；上传图片或文件时需同时传入
        cos_url、cos_key、file_name、file_size，此时 content 可为空。

        Args:
            member_nickname: 成员昵称（必填）
            context_type_level_one: 上下文1级分类，如"学习"、"健康"、"生活"（必填）
            context_type_level_two: 上下文2级分类，如"数学"、"体检报告"（必填）
            content: 文字内容（文字类型必填；图片/文件类型可选）
            record_id: 记录ID（选填，传入时执行更新操作）
            member_name: 成员名称（选填，未填时从相同昵称历史记录获取）
            context_type_level_three: 上下文3级分类（选填）
            context_type_level_four: 上下文4级分类（选填）
            cos_url: COS 资源 URL（上传图片/文件时必填）
            cos_key: COS 对象 Key（上传图片/文件时必填）
            file_name: 原始文件名（上传图片/文件时必填）
            file_size: 文件大小，单位字节（上传图片/文件时必填）
            permission: 访问权限，1-私有，2-家庭成员可见，3-全部成员可编辑（默认1）
            remark: 备注说明（选填）
            tags: 标签列表，多个标签用逗号分隔，如"重要,待复习"（选填，传入时全量替换）
        """
        try:
            # ── 判断内容格式 ──────────────────────────────────────────
            has_file = any(v is not None for v in [cos_url, cos_key, file_name])
            if has_file:
                missing = [
                    field_name for field_name, val in [
                        ("cos_url", cos_url),
                        ("cos_key", cos_key),
                        ("file_name", file_name),
                        ("file_size", file_size),
                    ] if val is None
                ]
                if missing:
                    return {"error": f"上传文件/图片时以下字段不能为空: {', '.join(missing)}"}

                image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
                ext = ""
                if file_name:
                    idx = file_name.rfind(".")
                    if idx != -1:
                        ext = file_name[idx:].lower()
                content_format = ContentFormat.IMAGE if ext in image_exts else ContentFormat.FILE
            else:
                if not record_id and not content:
                    return {"error": "文字内容 content 不能为空"}
                content_format = ContentFormat.TEXT

            # ── 更新模式 ──────────────────────────────────────────────
            if record_id is not None:
                update_fields: dict = {}
                if member_nickname:
                    update_fields["member_nickname"] = member_nickname
                if member_name:
                    update_fields["member_name"] = member_name
                if context_type_level_one:
                    update_fields["context_type_level_one"] = context_type_level_one
                if context_type_level_two:
                    update_fields["context_type_level_two"] = context_type_level_two
                if context_type_level_three is not None:
                    update_fields["context_type_level_three"] = context_type_level_three
                if context_type_level_four is not None:
                    update_fields["context_type_level_four"] = context_type_level_four
                if content_format is not None:
                    update_fields["content_format"] = int(content_format)
                if content is not None:
                    update_fields["content"] = content
                if cos_url is not None:
                    update_fields["cos_url"] = cos_url
                if cos_key is not None:
                    update_fields["cos_key"] = cos_key
                if file_name is not None:
                    update_fields["file_name"] = file_name
                if file_size is not None:
                    update_fields["file_size"] = file_size
                if remark is not None:
                    update_fields["remark"] = remark
                # tags 传入时直接写字段，同步到标签字典表
                if tags is not None:
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                    update_fields["tags"] = ",".join(tag_list)
                    tag_dao.ensure_tags_exist(tag_list)

                success = member_context_dao.update_context(record_id, update_fields)
                if not success:
                    return {"error": f"未找到 ID={record_id} 的记录或无字段需要更新"}

                # 同步更新向量索引（失败不影响主流程）
                latest = member_context_dao.get_context_by_id(record_id)
                if latest:
                    vector_index.upsert_record(record_id, latest)

                return {"success": True, "id": record_id, "updated_fields": list(update_fields.keys())}

            # ── 新增模式 ──────────────────────────────────────────────
            # 校验昵称是否在成员列表中
            valid_nicknames = member_info_dao.list_member_nicknames()
            if member_nickname not in valid_nicknames:
                return {"error": f"昵称 '{member_nickname}' 不存在，请先在成员列表中创建该成员"}

            # 校验 1级、2级分类必须存在于维度表
            if not context_category_dao.exists(context_type_level_one, context_type_level_two):
                return {
                    "error": f"分类 '{context_type_level_one}/{context_type_level_two}' 不存在，"
                             f"请先在分类维度表中维护一级和二级分类"
                }

            # 3级、4级分类：有传值时若不存在则自动创建
            l3 = context_type_level_three or ""
            l4 = context_type_level_four or ""
            if l3:
                context_category_dao.ensure_exists(
                    context_type_level_one, context_type_level_two, l3, l4
                )

            if not member_name:
                resolved_name = member_context_dao.get_latest_member_name(member_nickname)
                member_name = resolved_name if resolved_name else member_nickname

            # 处理标签：写入前同步到字典表
            tags_str = ""
            if tags:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                tags_str = ",".join(tag_list)
                tag_dao.ensure_tags_exist(tag_list)

            new_id = member_context_dao.insert_context(
                member_nickname=member_nickname,
                member_name=member_name,
                context_type_level_one=context_type_level_one,
                context_type_level_two=context_type_level_two,
                context_type_level_three=context_type_level_three or "",
                context_type_level_four=context_type_level_four or "",
                content_format=content_format,
                content=content,
                cos_url=cos_url,
                cos_key=cos_key,
                file_name=file_name,
                file_size=file_size or 0,
                status=ContextStatus.NORMAL,
                permission=ContextPermission(permission),
                remark=remark or "",
                tags=tags_str,
            )

            type_path = "/".join(
                p for p in [
                    context_type_level_one,
                    context_type_level_two,
                    context_type_level_three,
                    context_type_level_four,
                ] if p
            )

            # 写入向量索引（失败不影响主流程）
            vector_index.upsert_record(new_id, {
                "member_nickname": member_nickname,
                "member_name": member_name,
                "context_type_level_one": context_type_level_one,
                "context_type_level_two": context_type_level_two,
                "context_type_level_three": context_type_level_three or "",
                "context_type_level_four": context_type_level_four or "",
                "content": content,
                "remark": remark or "",
                "tags": tags_str,
                "file_name": file_name or "",
            })

            return {
                "success": True,
                "id": new_id,
                "member_nickname": member_nickname,
                "member_name": member_name,
                "context_type_path": type_path,
                "tags": tags_str,
            }

        except Exception as e:
            logger.error(f"存储上下文记录时发生错误: {e}")
            return {"error": f"存储失败: {str(e)}"}

    @mcp.tool()
    def query_member_context(
        record_id: Optional[int] = None,
        member_nickname: Optional[str] = None,
        member_name: Optional[str] = None,
        context_type_level_one: Optional[str] = None,
        context_type_level_two: Optional[str] = None,
        context_type_level_three: Optional[str] = None,
        context_type_level_four: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        """查询家庭成员上下文记录

        支持按 ID 精确查询，或按成员昵称/名称、上下文分类条件查询。
        COS 图片/文件记录将自动生成 5 分钟有效的预签名下载链接。

        Args:
            record_id: 记录ID（选填，传入时忽略其他条件，直接按ID查询）
            member_nickname: 成员昵称（选填）
            member_name: 成员名称（选填）
            context_type_level_one: 1级分类过滤，如"学习"、"健康"（条件查询时必填）
            context_type_level_two: 2级分类过滤（条件查询时必填）
            context_type_level_three: 3级分类过滤（条件查询时必填）
            context_type_level_four: 4级分类过滤（选填）
            keyword: 关键词模糊匹配，命中 4级分类/备注/标签 任一即返回（选填）
            page: 页码，从1开始（默认1）
            page_size: 每页条数（默认20，最大100）
        """
        try:
            # ── 按 ID 精确查询 ─────────────────────────────────────────
            if record_id is not None:
                row = member_context_dao.get_context_by_id(record_id)
                if not row:
                    return {"error": f"未找到 ID={record_id} 的记录"}
                return {"success": True, "record": _format_record(row)}

            # ── 条件查询 ───────────────────────────────────────────────
            if not member_nickname and not member_name:
                return {"error": "请至少传入 record_id、member_nickname 或 member_name 之一"}
            if not context_type_level_one or not context_type_level_two or not context_type_level_three:
                return {"error": "条件查询必须同时传入 context_type_level_one/two/three（1/2/3级分类）"}

            result = member_context_dao.query_contexts(
                member_nickname=member_nickname,
                member_name=member_name,
                context_type_level_one=context_type_level_one,
                context_type_level_two=context_type_level_two,
                context_type_level_three=context_type_level_three,
                context_type_level_four=context_type_level_four,
                keyword=keyword,
                page=page,
                page_size=page_size,
            )

            result["records"] = [_format_record(r) for r in result["records"]]
            return {"success": True, **result}

        except Exception as e:
            logger.error(f"查询上下文记录时发生错误: {e}")
            return {"error": f"查询失败: {str(e)}"}

    @mcp.tool()
    def get_member_context_summary(member_nickname: str):
        """查询某成员拥有哪些分类的上下文

        返回该成员所有不重复的四级分类路径及每个分类下的记录数量。

        Args:
            member_nickname: 成员昵称（必填）
        """
        try:
            rows = member_context_dao.get_context_type_summary(member_nickname)

            # 聚合为树形结构
            tree: dict = {}
            for row in rows:
                l1 = row["context_type_level_one"] or ""
                l2 = row["context_type_level_two"] or ""
                l3 = row["context_type_level_three"] or ""
                l4 = row["context_type_level_four"] or ""
                count = row["count"]
                path = "/".join(p for p in [l1, l2, l3, l4] if p)

                if l1 not in tree:
                    tree[l1] = {"count": 0, "children": {}}
                tree[l1]["count"] += count

                if l2 not in tree[l1]["children"]:
                    tree[l1]["children"][l2] = {"count": 0, "children": {}}
                tree[l1]["children"][l2]["count"] += count

                key3 = l3 or "__root__"
                if key3 not in tree[l1]["children"][l2]["children"]:
                    tree[l1]["children"][l2]["children"][key3] = {"count": 0, "children": {}}
                tree[l1]["children"][l2]["children"][key3]["count"] += count

                key4 = l4 or "__root__"
                tree[l1]["children"][l2]["children"][key3]["children"][key4] = count

            # 扁平列表（便于 AI 直接读取）
            flat = [
                {
                    "context_type_path": "/".join(
                        p for p in [
                            row["context_type_level_one"],
                            row["context_type_level_two"],
                            row["context_type_level_three"],
                            row["context_type_level_four"],
                        ] if p
                    ),
                    "level_one": row["context_type_level_one"],
                    "level_two": row["context_type_level_two"],
                    "level_three": row["context_type_level_three"] or "",
                    "level_four": row["context_type_level_four"] or "",
                    "count": row["count"],
                }
                for row in rows
            ]

            return {
                "success": True,
                "member_nickname": member_nickname,
                "total_records": sum(r["count"] for r in flat),
                "category_count": len(flat),
                "categories": flat,
            }

        except Exception as e:
            logger.error(f"查询上下文分类汇总时发生错误: {e}")
            return {"error": f"查询失败: {str(e)}"}

    @mcp.tool()
    def list_members():
        """获取所有家庭成员昵称列表"""
        try:
            nicknames = member_info_dao.list_member_nicknames()
            return {"success": True, "total": len(nicknames), "members": nicknames}
        except Exception as e:
            logger.error(f"查询成员列表时发生错误: {e}")
            return {"error": f"查询失败: {str(e)}"}

    @mcp.tool()
    def list_context_categories():
        """查询所有上下文分类

        返回完整分类列表，并明确说明分类约束规则：
        - 1级、2级分类：写入上下文时必须存在，不可自动创建
        - 3级、4级分类：写入上下文时若不存在会自动创建
        """
        try:
            rows = context_category_dao.list_all()

            # 按 level_one/level_two 分组聚合，便于展示
            grouped: dict = {}
            for row in rows:
                l1 = row["level_one"]
                l2 = row["level_two"]
                l3 = row["level_three"] or ""
                l4 = row["level_four"] or ""

                if l1 not in grouped:
                    grouped[l1] = {}
                if l2 not in grouped[l1]:
                    grouped[l1][l2] = []
                if l3:
                    grouped[l1][l2].append(
                        {"level_three": l3, "level_four": l4} if l4
                        else {"level_three": l3}
                    )

            # 转换为列表结构
            categories = []
            for l1, l2_map in grouped.items():
                l2_list = []
                for l2, sub in l2_map.items():
                    l2_list.append({"level_two": l2, "sub_categories": sub})
                categories.append({"level_one": l1, "level_two_list": l2_list})

            return {
                "success": True,
                "total": len(rows),
                "constraint_rule": {
                    "level_one_and_two": "写入时必须存在，不可自动创建，请从列表中选择",
                    "level_three_and_four": "写入时若不存在会自动创建到分类维度表"
                },
                "categories": categories,
            }

        except Exception as e:
            logger.error(f"查询分类列表时发生错误: {e}")
            return {"error": f"查询失败: {str(e)}"}




def _format_record(row: dict) -> dict:
    """格式化单条记录，COS 文件自动附加预签名下载链接"""
    content_format = row.get("content_format", 1)
    cos_key = row.get("cos_key")

    download_url = ""
    if content_format in (ContentFormat.IMAGE, ContentFormat.FILE) and cos_key:
        download_url = get_presigned_url(cos_key, expires=300)

    created_at = row.get("created_at")
    updated_at = row.get("updated_at")

    return {
        "id": row.get("id"),
        "member_nickname": row.get("member_nickname"),
        "member_name": row.get("member_name"),
        "context_type_path": "/".join(
            p for p in [
                row.get("context_type_level_one", ""),
                row.get("context_type_level_two", ""),
                row.get("context_type_level_three", ""),
                row.get("context_type_level_four", ""),
            ] if p
        ),
        "context_type_level_one": row.get("context_type_level_one"),
        "context_type_level_two": row.get("context_type_level_two"),
        "context_type_level_three": row.get("context_type_level_three"),
        "context_type_level_four": row.get("context_type_level_four"),
        "content_format": content_format,
        "content": row.get("content"),
        "file_name": row.get("file_name"),
        "file_size": row.get("file_size"),
        "cos_url": row.get("cos_url"),
        "download_url": download_url,
        "permission": row.get("permission"),
        "remark": row.get("remark"),
        "tags": [t for t in (row.get("tags") or "").split(",") if t],
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else None,
        "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S") if updated_at else None,
    }
