"""安全与认证相关的工具函数。

包含：
- 密码哈希/校验（SHA-256 预哈希 + bcrypt，解决 72 字节限制）
- Access Token 生成/验证
- Refresh Token 生成/验证
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# 新格式哈希前缀
SHA256_PREFIX = "sha256$"


def _sha256_prehash(password: str) -> str:
    """对密码进行 SHA-256 预哈希。

    bcrypt 限制密码最多 72 字节。SHA-256 预哈希产生固定 64 字节的
    hex 摘要，始终在 72 字节以内，彻底解决长度限制问题。
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希值是否匹配。

    统一使用 SHA-256 预哈希方案，彻底解决 bcrypt 72 字节限制。
    哈希格式：sha256$<bcrypt_hash>
    """
    if not hashed_password.startswith(SHA256_PREFIX):
        raise ValueError("密码哈希格式无效，缺少 sha256$ 前缀。" "请重新注册或联系管理员重置密码。")
    bcrypt_hash = hashed_password[len(SHA256_PREFIX) :]
    prehashed = _sha256_prehash(plain_password)
    return bcrypt.checkpw(prehashed.encode("utf-8"), bcrypt_hash.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """对密码进行哈希加密。

    使用 SHA-256 预哈希 + bcrypt 的双层方案：
    1. SHA-256 将任意长度密码转为固定 64 字节摘要
    2. bcrypt 对摘要进行加盐哈希
    3. 返回 sha256$<bcrypt_hash> 格式
    """
    prehashed = _sha256_prehash(password)
    bcrypt_hash = bcrypt.hashpw(prehashed.encode("utf-8"), bcrypt.gensalt())
    return f"{SHA256_PREFIX}{bcrypt_hash.decode('utf-8')}"


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """生成 Access Token（短期有效，默认 1 小时）。"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """生成 Refresh Token（长期有效，默认 7 天）。

    Refresh Token 额外包含 jti（唯一 ID）用于服务端黑名单。
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # 生成唯一 jti 用于黑名单
    jti = secrets.token_urlsafe(32)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh", "jti": jti}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """解码并验证 JWT Token，返回 payload 或 None。"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def get_token_expire_seconds(token: str) -> int:
    """获取 Token 剩余有效秒数。

    用于设置 Cookie 的 max_age 和黑名单 TTL。
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        if exp:
            now = datetime.now(timezone.utc)
            remaining = exp - int(now.timestamp())
            return max(remaining, 0)
    except JWTError:
        pass
    return 0
