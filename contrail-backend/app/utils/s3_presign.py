"""
S3/MinIO Presigned URL 工具

目标：
- 数据库仅保存 Object Key（相对路径/文件名）
- 后端在返回 DTO 时生成临时可访问的 Presigned URL（默认 1 小时）

依赖：
- minio
"""

import logging
from typing import Optional
from datetime import timedelta

from flask import current_app
from app.utils.minio_storage import get_minio_client

logger = logging.getLogger(__name__)


def presign_get_object_url(object_key: str, expires_in: Optional[int] = None) -> Optional[str]:
    """
    为指定 object key 生成 get_object 的 Presigned URL。

    Args:
        object_key: 数据库保存的 Object Key，如 "2024/01/user_123_uuid.jpg"
        expires_in: 过期秒数；不传则读取 MINIO_PRESIGN_EXPIRES（默认 3600）

    Returns:
        成功返回完整 URL；失败返回 None（不会抛到 API 层导致接口崩溃）。
    """
    if not object_key:
        return None

    try:
        bucket = current_app.config.get("MINIO_BUCKET") or "student-certificates"
        exp = int(expires_in or current_app.config.get("MINIO_PRESIGN_EXPIRES") or 3600)
        client = get_minio_client()
        return client.presigned_get_object(bucket, object_key, expires=timedelta(seconds=exp))
    except Exception:
        # 只记录日志，不让异常穿透导致接口崩溃
        logger.exception("生成 Presigned URL 失败: key=%s", object_key)
        return None


