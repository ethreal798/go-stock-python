"""URL safety checks for user-provided upstream service endpoints."""

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

from app.config import settings


class BaseURLSafetyError(ValueError):
    """Raised when a user-provided base URL violates network safety rules."""


FORBIDDEN_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
}


async def validate_ai_base_url(base_url: str, resolve_host: bool = True) -> str:
    """Validate and normalize an OpenAI-compatible API base URL."""
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise BaseURLSafetyError("Base URL 不能为空")

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"}:
        raise BaseURLSafetyError("Base URL 仅支持 http 或 https")
    if parsed.scheme == "http" and not settings.AI_MODEL_CONFIG_ALLOW_HTTP_BASE_URL:
        raise BaseURLSafetyError("当前环境不允许使用 http Base URL")
    if not parsed.hostname:
        raise BaseURLSafetyError("Base URL 必须包含主机名")
    if parsed.username or parsed.password:
        raise BaseURLSafetyError("Base URL 不允许包含用户名或密码")
    if parsed.query or parsed.fragment:
        raise BaseURLSafetyError("Base URL 不允许包含 query 或 fragment")

    host = parsed.hostname.strip().lower()
    if _is_forbidden_hostname(host):
        raise BaseURLSafetyError("Base URL 不允许指向本机或元数据服务")

    try:
        port = parsed.port
    except ValueError as exc:
        raise BaseURLSafetyError("Base URL 端口不合法") from exc

    literal_ip = _parse_ip(host)
    if literal_ip is not None:
        _validate_ip_allowed(literal_ip)
    elif resolve_host:
        await _validate_resolved_addresses(host, port or _default_port(parsed.scheme))

    return normalized


def _is_forbidden_hostname(host: str) -> bool:
    return host in FORBIDDEN_HOSTS or host.endswith(".localhost")


def _parse_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _validate_ip_allowed(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if settings.AI_MODEL_CONFIG_ALLOW_PRIVATE_BASE_URL:
        return
    if not ip.is_global:
        raise BaseURLSafetyError("Base URL 不允许解析到内网、本机、链路本地或保留地址")


async def _validate_resolved_addresses(host: str, port: int) -> None:
    try:
        addr_info = await asyncio.to_thread(socket.getaddrinfo, host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise BaseURLSafetyError("Base URL 主机名无法解析") from exc

    if not addr_info:
        raise BaseURLSafetyError("Base URL 主机名无法解析")

    for item in addr_info:
        ip = ipaddress.ip_address(item[4][0])
        _validate_ip_allowed(ip)


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80
