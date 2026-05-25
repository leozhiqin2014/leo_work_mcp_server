"""
健康记录工具模块
"""

import logging
from typing import Optional

from datetime import datetime
import pytz

from dao import health_dao

logger = logging.getLogger(__name__)


def register_tools(mcp) -> None:
    """注册健康记录相关工具"""

    @mcp.tool()
    def query_health_records(
        member_nickname: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """查询家庭成员身高体重健康记录

        Args:
            member_nickname: 成员昵称（必填）
            start_date: 开始日期，格式 YYYY-MM-DD（可选）
            end_date: 结束日期，格式 YYYY-MM-DD（可选）
        """
        try:
            records = health_dao.query_records(member_nickname, start_date, end_date)

            result = {
                "member_nickname": member_nickname,
                "total_count": len(records),
                "date_range": {"start_date": start_date, "end_date": end_date},
                "records": [],
            }

            for record in records:
                result["records"].append({
                    "id": record["id"],
                    "member_name": record["member_name"],
                    "record_date": record["record_date"].strftime("%Y-%m-%d") if record["record_date"] else None,
                    "height_cm": float(record["height"]) if record["height"] else 0.0,
                    "weight_kg": float(record["weight"]) if record["weight"] else 0.0,
                    "bmi": float(record["bmi"]) if record["bmi"] else 0.0,
                    "body_fat_rate": float(record["body_fat_rate"]) if record["body_fat_rate"] else 0.0,
                    "created_at": record["created_at"].strftime("%Y-%m-%d %H:%M:%S") if record["created_at"] else None,
                })

            return result

        except Exception as e:
            logger.error(f"查询健康记录时发生错误: {e}")
            return {"error": f"查询失败: {str(e)}"}

    @mcp.tool()
    def add_health_record(
        member_nickname: str,
        weight: float,
        member_name: Optional[str] = None,
        record_date: Optional[str] = None,
        height: Optional[float] = None,
        bmi: Optional[float] = None,
        body_fat_rate: Optional[float] = None,
    ):
        """提交家庭成员身高体重健康记录

        Args:
            member_nickname: 成员昵称（必填）
            weight: 体重，单位kg（必填）
            member_name: 成员名称（选填，未填时从相同昵称记录获取）
            record_date: 记录日期，格式 YYYY-MM-DD（选填，默认当前时间-上海时区）
            height: 身高，单位cm（选填，未填时从相同昵称最近记录获取）
            bmi: BMI指数（选填，未填时按公式计算）
            body_fat_rate: 体脂率（选填）
        """
        try:
            # 查询最新历史记录，补全 member_name 和 height
            last_record = health_dao.get_latest_record_by_nickname(member_nickname)

            # 处理 member_name
            if not member_name or member_name.strip() == "":
                if last_record and last_record.get("member_name"):
                    member_name = last_record["member_name"]
                else:
                    return {"error": f"未找到昵称 '{member_nickname}' 的历史记录，请提供成员名称"}

            # 处理 record_date
            if not record_date or record_date.strip() == "":
                shanghai_tz = pytz.timezone("Asia/Shanghai")
                record_date = datetime.now(shanghai_tz).strftime("%Y-%m-%d")

            # 处理 height
            if height is None:
                if last_record and last_record.get("height"):
                    height = float(last_record["height"])
                else:
                    return {"error": f"未找到昵称 '{member_nickname}' 的历史身高记录，请提供身高"}

            # 处理 bmi
            if bmi is None:
                height_m = height / 100
                bmi = round(weight / (height_m ** 2), 2)

            # 处理 body_fat_rate
            if body_fat_rate is None:
                body_fat_rate = 0.0

            new_id = health_dao.insert_record(
                member_name=member_name,
                member_nickname=member_nickname,
                record_date=record_date,
                height=height,
                weight=weight,
                bmi=bmi,
                body_fat_rate=body_fat_rate,
            )

            return {
                "success": True,
                "id": new_id,
                "member_nickname": member_nickname,
                "member_name": member_name,
                "record_date": record_date,
                "height_cm": height,
                "weight_kg": weight,
                "bmi": bmi,
                "body_fat_rate": body_fat_rate,
            }

        except Exception as e:
            logger.error(f"提交健康记录时发生错误: {e}")
            return {"error": f"提交失败: {str(e)}"}
