import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = BACKEND_ROOT / "logs"
DEFAULT_LOG_FILE = LOG_DIR / "app.log"


def configure_logging(log_file: Path | str | None = None) -> Path:
    log_path = Path(log_file) if log_file is not None else DEFAULT_LOG_FILE
    if not log_path.is_absolute():
        log_path = LOG_DIR / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            log_path,
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        ),
    ]

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
    return log_path
