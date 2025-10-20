import logging
import sys

DEFAULT_FORMAT = "%(asctime)s %(levelname).1s %(name)s - %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"

_configured = False

def setup_logging(level: int = logging.INFO) -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATEFMT)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    # Remove existing handlers to avoid duplicate logs when reloading
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet noisy third-party loggers if needed
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("telebot").setLevel(logging.INFO)

    _configured = True
