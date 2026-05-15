from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.processors import TimeStamper


def setup_logging(level: str = "INFO") -> None:
    timestamper = TimeStamper(fmt="iso", utc=True)

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer() if level == "DEBUG"
            else structlog.processors.JSONRenderer(serializer=_custom_json_serializer),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    for lib in ("uvicorn", "uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def _custom_json_serializer(data: Dict[str, Any], **kwargs: Any) -> str:
    return json.dumps(data, default=str, ensure_ascii=False)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name or __name__)


logger = get_logger("govscheme")
