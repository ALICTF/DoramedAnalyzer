import logging
from typing import Any, Optional
from core.settings import get_settings


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def setup_logging(level: Optional[str] = None) -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    log_level = (level or get_settings().log_level).upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(component: str) -> logging.Logger:
    return logging.getLogger(f"dstand.ai.{component}")


def reason(exc: BaseException) -> str:
    message = str(exc).strip()
    if message:
        return message
    return exc.__class__.__name__


def compact_error(
    logger: logging.Logger,
    event: str,
    exc: BaseException,
    *,
    level: int = logging.ERROR,
    **context: Any,
) -> None:
    context_text = _format_context(context)
    logger.log(level, "%s failed. reason=%s%s", event, reason(exc), context_text)


def compact_warning(
    logger: logging.Logger,
    event: str,
    exc: BaseException,
    **context: Any,
) -> None:
    compact_error(logger, event, exc, level=logging.WARNING, **context)


def _format_context(context: dict[str, Any]) -> str:
    clean_items = {
        key: value
        for key, value in context.items()
        if value is not None and value != ""
    }
    if not clean_items:
        return ""
    values = " ".join(f"{key}={value}" for key, value in clean_items.items())
    return f" {values}"
