"""
MinIO 存储工具

包含：
- MinIO client 创建（从 Flask app.config 读取配置）
- 上传对象（put_object），用于后端中转上传模式
"""

import io
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

from flask import current_app
from minio import Minio

logger = logging.getLogger(__name__)


def get_minio_client() -> Minio:
    """
    创建 MinIO client（S3 协议兼容）。

    配置来自 app.config：
    - MINIO_ENDPOINT: http(s)://host:port 或 host:port
    - MINIO_ACCESS_KEY / MINIO_SECRET_KEY
    - MINIO_SECURE: True/False/None（None 表示从 endpoint scheme 推断）
    - MINIO_REGION: 建议配置，避免 SDK presign 时触发 region 探测
    """
    endpoint = current_app.config.get("MINIO_ENDPOINT")
    access_key = current_app.config.get("MINIO_ACCESS_KEY")
    secret_key = current_app.config.get("MINIO_SECRET_KEY")
    region = current_app.config.get("MINIO_REGION") or None

    if not access_key or not secret_key:
        raise ValueError("MinIO access key/secret key 未配置（请设置 MINIO_ACCESS_KEY / MINIO_SECRET_KEY）")

    parsed = urlparse(endpoint or "")
    host = (parsed.netloc or parsed.path or "").strip() or (endpoint or "").strip()
    if not host:
        raise ValueError("MinIO endpoint 未配置（请设置 MINIO_ENDPOINT）")

    secure_cfg = current_app.config.get("MINIO_SECURE")
    if secure_cfg in (True, False):
        secure = bool(secure_cfg)
    else:
        secure = (parsed.scheme == "https")

    return Minio(
        host,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
        region=region,
    )


def upload_bytes(
    object_key: str,
    data: bytes,
    content_type: Optional[str],
    bucket: Optional[str] = None,
) -> Tuple[str, int]:
    """
    上传 bytes 到 MinIO，并返回 (object_key, size)。
    """
    if not object_key:
        raise ValueError("object_key 不能为空")
    if data is None or len(data) == 0:
        raise ValueError("上传文件为空")

    bkt = bucket or current_app.config.get("MINIO_BUCKET") or "student-certificates"
    client = get_minio_client()

    bio = io.BytesIO(data)
    client.put_object(
        bkt,
        object_key,
        bio,
        length=len(data),
        content_type=content_type or "application/octet-stream",
    )
    return object_key, len(data)



