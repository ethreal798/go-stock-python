"""Application logging configuration and HTTP access logging."""

from __future__ import annotations

import json
import logging
import logging.config
import re
import time
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import settings

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
_SAFE_SERVICE_NAME = re.compile(r"[^a-zA-Z0-9_.-]+")
_SAFE_REQUEST_ID = re.compile(r"^[a-zA-Z0-9_.:-]{1,128}$")


class RequestContextFilter(logging.Filter):
    """Attach request-scoped fields to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        record.service = settings.LOG_SERVICE_NAME
        return True


class JsonFormatter(logging.Formatter):
    """Produce one JSON object per line for reliable parsing and shipping."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).astimezone().isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "service": getattr(record, "service", settings.LOG_SERVICE_NAME),
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        for field in ("method", "path", "status_code", "duration_ms", "client_ip"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging() -> Path | None:
    """Configure stdout and an optional daily rotating persistent log file."""

    handlers: dict[str, dict[str, Any]] = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": settings.LOG_FORMAT,
            "filters": ["request_context"],
        }
    }
    selected_handlers = ["console"]
    log_path: Path | None = None
    if settings.LOG_TO_FILE:
        log_dir = Path(settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        service_name = _SAFE_SERVICE_NAME.sub("-", settings.LOG_SERVICE_NAME).strip(".-") or "app"
        log_path = log_dir / f"{service_name}.log"
        handlers["file"] = {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_path),
            "when": "midnight",
            "interval": 1,
            "backupCount": settings.LOG_RETENTION_DAYS,
            "encoding": "utf-8",
            "delay": True,
            "formatter": settings.LOG_FORMAT,
            "filters": ["request_context"],
        }
        selected_handlers.append("file")

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"request_context": {"()": RequestContextFilter}},
            "formatters": {
                "json": {"()": JsonFormatter},
                "text": {"format": "%(asctime)s %(levelname)s [%(service)s] [%(request_id)s] %(name)s: %(message)s"},
            },
            "handlers": handlers,
            "root": {"level": settings.LOG_LEVEL.upper(), "handlers": selected_handlers},
            "loggers": {
                "uvicorn": {"level": settings.LOG_LEVEL.upper(), "handlers": selected_handlers, "propagate": False},
                "uvicorn.error": {
                    "level": settings.LOG_LEVEL.upper(),
                    "handlers": selected_handlers,
                    "propagate": False,
                },
                "uvicorn.access": {"level": "WARNING", "handlers": selected_handlers, "propagate": False},
            },
        }
    )
    return log_path


class RequestLoggingMiddleware:
    """Log HTTP status and latency, and propagate a correlation ID."""

    def __init__(self, app: Any) -> None:
        self.app = app
        self.logger = logging.getLogger("app.access")

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        supplied_id = headers.get(b"x-request-id", b"").decode("ascii", errors="ignore")
        request_id = supplied_id if _SAFE_REQUEST_ID.fullmatch(supplied_id) else uuid4().hex
        token = request_id_context.set(request_id)
        started_at = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            self._write_access_log(scope, status_code, started_at, level=logging.ERROR, exc_info=True)
            raise
        else:
            level = logging.WARNING if status_code >= 400 else logging.INFO
            self._write_access_log(scope, status_code, started_at, level=level)
        finally:
            request_id_context.reset(token)

    def _write_access_log(
        self,
        scope: dict[str, Any],
        status_code: int,
        started_at: float,
        *,
        level: int,
        exc_info: bool = False,
    ) -> None:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        client = scope.get("client")
        self.logger.log(
            level,
            "%s %s %s %.2fms",
            scope.get("method", "-"),
            scope.get("path", "-"),
            status_code,
            duration_ms,
            exc_info=exc_info,
            extra={
                "method": scope.get("method", "-"),
                "path": scope.get("path", "-"),
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client[0] if client else "-",
            },
        )


__all__ = ["JsonFormatter", "RequestLoggingMiddleware", "setup_logging"]
