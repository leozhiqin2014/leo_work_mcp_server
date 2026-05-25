"""
家庭成员上下文记录表实体模型
对应数据库表: member_context
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Optional


class ContentFormat(IntEnum):
    """内容格式枚举"""
    TEXT = 1    # 文字
    IMAGE = 2   # 图片
    FILE = 3    # 文件


class ContextStatus(IntEnum):
    """记录状态枚举"""
    NORMAL = 1    # 正常
    DELETED = 2   # 已删除（软删除）
    ARCHIVED = 3  # 已归档


class ContextPermission(IntEnum):
    """访问权限枚举"""
    PRIVATE = 1         # 私有（仅自己）
    FAMILY_VISIBLE = 2  # 家庭成员可见
    FAMILY_EDITABLE = 3 # 全部成员可编辑


@dataclass
class MemberContext:
    """
    家庭成员上下文记录实体

    对应数据库表: member_context
    """
    # 主键（新建时可为 None）
    id: Optional[int] = None

    # 成员信息
    member_nickname: str = ""       # 成员昵称
    member_name: str = ""           # 成员名称

    # 上下文分类（最多四级）
    context_type_level_one: str = ""    # 1级分类：学习/健康/生活等
    context_type_level_two: str = ""    # 2级分类：如数学、英语、体检报告等
    context_type_level_three: str = ""  # 3级分类
    context_type_level_four: str = ""   # 4级分类

    # 内容信息
    content_format: ContentFormat = ContentFormat.TEXT  # 内容格式：1-文字，2-图片，3-文件
    content: Optional[str] = None       # 文字内容（content_format=1 时使用）

    # COS 资源信息（content_format=2,3 时使用）
    cos_url: Optional[str] = None       # COS 资源 URL
    cos_key: Optional[str] = None       # COS 对象 Key
    file_name: Optional[str] = None     # 原始文件名
    file_size: int = 0                  # 文件大小（字节）

    # 状态与权限
    status: ContextStatus = ContextStatus.NORMAL
    permission: ContextPermission = ContextPermission.PRIVATE

    # 备注
    remark: str = ""

    # 时间戳（由数据库自动维护）
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_text(self) -> bool:
        """是否为文字内容"""
        return self.content_format == ContentFormat.TEXT

    def is_image(self) -> bool:
        """是否为图片内容"""
        return self.content_format == ContentFormat.IMAGE

    def is_file(self) -> bool:
        """是否为文件内容"""
        return self.content_format == ContentFormat.FILE

    def is_active(self) -> bool:
        """是否为正常状态"""
        return self.status == ContextStatus.NORMAL

    def is_deleted(self) -> bool:
        """是否已软删除"""
        return self.status == ContextStatus.DELETED

    def is_archived(self) -> bool:
        """是否已归档"""
        return self.status == ContextStatus.ARCHIVED

    def context_type_path(self) -> str:
        """返回拼接的分类路径，如 '学习/数学'"""
        parts = [
            self.context_type_level_one,
            self.context_type_level_two,
            self.context_type_level_three,
            self.context_type_level_four,
        ]
        return "/".join(p for p in parts if p)

    @classmethod
    def from_db_row(cls, row: dict) -> "MemberContext":
        """从数据库查询结果字典构造实体"""
        return cls(
            id=row.get("id"),
            member_nickname=row.get("member_nickname", ""),
            member_name=row.get("member_name", ""),
            context_type_level_one=row.get("context_type_level_one", ""),
            context_type_level_two=row.get("context_type_level_two", ""),
            context_type_level_three=row.get("context_type_level_three", ""),
            context_type_level_four=row.get("context_type_level_four", ""),
            content_format=ContentFormat(row.get("content_format", 1)),
            content=row.get("content"),
            cos_url=row.get("cos_url"),
            cos_key=row.get("cos_key"),
            file_name=row.get("file_name"),
            file_size=row.get("file_size", 0),
            status=ContextStatus(row.get("status", 1)),
            permission=ContextPermission(row.get("permission", 1)),
            remark=row.get("remark", ""),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def to_dict(self) -> dict:
        """转换为字典（用于 JSON 序列化或日志）"""
        return {
            "id": self.id,
            "member_nickname": self.member_nickname,
            "member_name": self.member_name,
            "context_type_level_one": self.context_type_level_one,
            "context_type_level_two": self.context_type_level_two,
            "context_type_level_three": self.context_type_level_three,
            "context_type_level_four": self.context_type_level_four,
            "context_type_path": self.context_type_path(),
            "content_format": self.content_format.value,
            "content_format_label": self.content_format.name,
            "content": self.content,
            "cos_url": self.cos_url,
            "cos_key": self.cos_key,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "status": self.status.value,
            "status_label": self.status.name,
            "permission": self.permission.value,
            "permission_label": self.permission.name,
            "remark": self.remark,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
