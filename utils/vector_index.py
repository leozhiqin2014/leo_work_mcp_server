"""
成员上下文向量索引模块

负责把成员上下文记录文本向量化，并写入 COS Vectors 桶。
密钥/配置全部从环境变量读取：
  VECTOR_COS_SECRET_ID
  VECTOR_COS_SECRET_KEY
  VECTOR_COS_BUCKET            如 "openclaw-1253134116"
  VECTOR_COS_REGION            如 "ap-guangzhou"
  VECTOR_COS_INDEX             如 "member-context-index"
  VECTOR_EMBEDDING_BASE_URL    如 "https://api.siliconflow.cn/v1"
  VECTOR_EMBEDDING_API_KEY
  VECTOR_EMBEDDING_MODEL       如 "Qwen/Qwen3-Embedding-8B"
  VECTOR_COS_DOMAIN            选填，默认 vectors.{REGION}.coslake.com
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── 环境变量读取 ──────────────────────────────────────────────────
SECRET_ID = os.getenv("VECTOR_COS_SECRET_ID", "")
SECRET_KEY = os.getenv("VECTOR_COS_SECRET_KEY", "")
BUCKET = os.getenv("VECTOR_COS_BUCKET", "")
REGION = os.getenv("VECTOR_COS_REGION", "ap-guangzhou")
INDEX = os.getenv("VECTOR_COS_INDEX", "member-context-index")
DOMAIN = os.getenv("VECTOR_COS_DOMAIN", f"vectors.{REGION}.coslake.com")

EMBEDDING_BASE_URL = os.getenv("VECTOR_EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_API_KEY = os.getenv("VECTOR_EMBEDDING_API_KEY", "")
EMBEDDING_MODEL = os.getenv("VECTOR_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-8B")

# ── 客户端懒加载 ──────────────────────────────────────────────────
_embed_client = None
_vclient = None


def _ensure_clients() -> bool:
    """初始化 embedding / cos vectors 客户端。配置不全或依赖缺失时返回 False。"""
    global _embed_client, _vclient
    if _embed_client is not None and _vclient is not None:
        return True

    if not all([SECRET_ID, SECRET_KEY, BUCKET, EMBEDDING_API_KEY]):
        logger.warning("向量索引配置不完整，跳过向量写入（需要 VECTOR_COS_*/VECTOR_EMBEDDING_* 环境变量）")
        return False

    try:
        from openai import OpenAI
        from qcloud_cos import CosConfig, CosVectorsClient
    except ImportError as e:
        logger.warning(f"向量索引依赖缺失，跳过：{e}")
        return False

    _embed_client = OpenAI(base_url=EMBEDDING_BASE_URL, api_key=EMBEDDING_API_KEY)
    _vclient = CosVectorsClient(
        CosConfig(Region=REGION, SecretId=SECRET_ID, SecretKey=SECRET_KEY,
                  Scheme="https", Domain=DOMAIN)
    )
    return True


def _build_text(record: dict) -> str:
    """将记录拼装为待向量化文本。"""
    parts = []
    for key in ("member_name", "member_nickname"):
        v = record.get(key)
        if v:
            parts.append(str(v))

    type_path = "/".join(
        p for p in [
            record.get("context_type_level_one"),
            record.get("context_type_level_two"),
            record.get("context_type_level_three"),
            record.get("context_type_level_four"),
        ] if p
    )
    if type_path:
        parts.append(type_path)

    for key in ("remark", "tags", "content", "file_name"):
        v = record.get(key)
        if v:
            parts.append(str(v))
    return "\n".join(parts)


def _vector_key(record_id: int) -> str:
    return f"member_ctx:{record_id}"


def upsert_record(record_id: int, record: dict) -> bool:
    """写入/覆盖单条上下文向量。失败不抛出，只记日志。"""
    if not _ensure_clients():
        return False

    text = _build_text(record)
    if not text.strip():
        logger.warning(f"记录 id={record_id} 文本为空，跳过向量写入")
        return False

    try:
        resp = _embed_client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
        emb = resp.data[0].embedding

        vector = {
            "key": _vector_key(record_id),
            "data": {"float32": emb},
            "metadata": {
                "record_id": int(record_id),
                "member_nickname": record.get("member_nickname") or "",
                "context_type_path": "/".join(
                    p for p in [
                        record.get("context_type_level_one"),
                        record.get("context_type_level_two"),
                        record.get("context_type_level_three"),
                        record.get("context_type_level_four"),
                    ] if p
                ),
            },
        }
        _vclient.put_vectors(Bucket=BUCKET, Index=INDEX, Vectors=[vector])
        logger.info(f"向量写入成功 record_id={record_id}")
        return True
    except Exception as e:
        logger.error(f"向量写入失败 record_id={record_id}: {e}")
        return False


def delete_record(record_id: int) -> bool:
    """删除单条向量。"""
    if not _ensure_clients():
        return False
    try:
        _vclient.delete_vectors(Bucket=BUCKET, Index=INDEX, Keys=[_vector_key(record_id)])
        return True
    except Exception as e:
        logger.error(f"向量删除失败 record_id={record_id}: {e}")
        return False
