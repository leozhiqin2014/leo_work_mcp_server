"""
腾讯云 COS 工具模块
"""

import os
import logging

logger = logging.getLogger(__name__)

# COS 配置从环境变量读取
COS_SECRET_ID = os.getenv("COS_SECRET_ID", "")
COS_SECRET_KEY = os.getenv("COS_SECRET_KEY", "")
COS_BUCKET = os.getenv("COS_BUCKET", "")
COS_REGION = os.getenv("COS_REGION", "ap-beijing")


def get_presigned_url(cos_key: str, expires: int = 300) -> str:
    """生成 COS 对象的预签名下载链接

    Args:
        cos_key: COS 对象 Key
        expires: 有效期秒数，默认 300（5分钟）

    Returns:
        预签名 URL 字符串，失败时返回空字符串
    """
    if not all([COS_SECRET_ID, COS_SECRET_KEY, COS_BUCKET]):
        logger.warning("COS 配置不完整，跳过生成预签名链接")
        return ""

    try:
        from qcloud_cos import CosConfig, CosS3Client

        config = CosConfig(
            Region=COS_REGION,
            SecretId=COS_SECRET_ID,
            SecretKey=COS_SECRET_KEY,
        )
        client = CosS3Client(config)

        url = client.get_presigned_download_url(
            Bucket=COS_BUCKET,
            Key=cos_key,
            Expired=expires,
        )
        return url
    except Exception as e:
        logger.error(f"生成 COS 预签名链接失败: {e}")
        return ""
