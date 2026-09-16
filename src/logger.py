import os
import sys
from pathlib import Path

from loguru import logger


ROOT = Path(__file__).resolve().parents[1]


def configure_logging() -> None:
    log_dir = Path(os.environ.get("LOG_DIR", str(ROOT / "logs")))
    log_dir.mkdir(parents=True, exist_ok=True)
    level = os.environ.get("LOG_LEVEL", "INFO").upper()

    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level.icon} {level:<8}</level> | {message}",
    )
    logger.add(
        log_dir / "canaan.log",
        level=level,
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level.icon} {level:<8} | {process.name} | {message}",
    )


configure_logging()

