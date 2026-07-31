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
from zoneinfo import ZoneInfo

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
            "timestamp": datetime.fromtimestamp(record.created, tz=ZoneInfo(settings.LOG_TIMEZONE)).isoformat(
                timespec="milliseconds"
            ),
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


class PrettyFormatter(logging.Formatter):
    """Compact human-readable formatter with optional ANSI colors."""

    RESET = "\033[0m"
    DIM = "\033[2m"
    LEVEL_COLORS = {
        "DEBUG": "\033[90m",
        "INFO": "\033[36m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }

    def __init__(self, *, color: bool = False) -> None:
        super().__init__()
        self.color = color
        self.timezone = ZoneInfo(settings.LOG_TIMEZONE)

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=self.timezone).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record.levelname.ljust(8)
        service = str(getattr(record, "service", settings.LOG_SERVICE_NAME))
        request_id = str(getattr(record, "request_id", "-"))
        separator = " | "

        if self.color:
            level_color = self.LEVEL_COLORS.get(record.levelname, "")
            prefix = (
                f"{self.DIM}{timestamp}{self.RESET}"
                f"{self.DIM}{separator}{self.RESET}"
                f"{level_color}{level}{self.RESET}"
                f"{self.DIM}{separator}{self.RESET}"
                f"\033[35m{service}{self.RESET}"
                f"{self.DIM}{separator}{self.RESET}"
                f"\033[34m{record.name}{self.RESET}"
            )
        else:
            prefix = separator.join((timestamp, level, service, record.name))

        if request_id != "-":
            prefix += f"{separator}req={request_id}"
        message = f"{prefix}{separator}{record.getMessage()}"
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        return message


def setup_logging() -> Path | None:
    """Configure stdout and an optional daily rotating persistent log file."""

    console_formatter = "json" if settings.LOG_FORMAT == "json" else "pretty_color"
    file_formatter = "json" if settings.LOG_FORMAT == "json" else "pretty"
    handlers: dict[str, dict[str, Any]] = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": console_formatter,
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
            "formatter": file_formatter,
            "filters": ["request_context"],
        }
        selected_handlers.append("file")

    configured_loggers: dict[str, dict[str, Any]] = {
        "uvicorn": {"level": settings.LOG_LEVEL.upper(), "handlers": selected_handlers, "propagate": False},
        "uvicorn.error": {
            "level": settings.LOG_LEVEL.upper(),
            "handlers": selected_handlers,
            "propagate": False,
        },
        "uvicorn.access": {"level": "WARNING", "handlers": selected_handlers, "propagate": False},
        "app.access": {
            "level": settings.ACCESS_LOG_LEVEL.upper(),
            "handlers": selected_handlers,
            "propagate": False,
        },
    }
    for logger_name, level in settings.LOG_LEVEL_OVERRIDES.items():
        configured_loggers[logger_name] = {"level": level, "handlers": [], "propagate": True}

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"request_context": {"()": RequestContextFilter}},
            "formatters": {
                "json": {"()": JsonFormatter},
                "pretty": {"()": PrettyFormatter, "color": False},
                "pretty_color": {"()": PrettyFormatter, "color": settings.LOG_COLOR},
            },
            "handlers": handlers,
            "root": {"level": settings.LOG_LEVEL.upper(), "handlers": selected_handlers},
            "loggers": configured_loggers,
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
        should_log = settings.ACCESS_LOG_ENABLED and scope.get("path") not in settings.ACCESS_LOG_EXCLUDE_PATHS

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
            if settings.ACCESS_LOG_ENABLED:
                self._write_access_log(scope, status_code, started_at, level=logging.ERROR, exc_info=True)
            raise
        else:
            # Excluded paths stay quiet when healthy, but their failures remain visible.
            if should_log or status_code >= 400:
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


__all__ = ["JsonFormatter", "PrettyFormatter", "RequestLoggingMiddleware", "setup_logging"]
