import logging
import sys
from pathlib import Path

from loguru import logger

from app.include.config import config


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}"


class InterceptHandler(logging.Handler):
    """Forward standard logging messages, including MCP SDK logs, to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    # MCP stdio reserves stdout for protocol messages.
    logger.add(sys.stderr, format=LOG_FORMAT, level=config.LOG_LEVEL)
    logger.add(
        LOG_DIR / "info.log",
        format=LOG_FORMAT,
        level="DEBUG",
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.DEBUG, force=True)


_setup_logging()
