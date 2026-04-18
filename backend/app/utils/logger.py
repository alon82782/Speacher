import sys
from loguru import logger as _logger


def setup_logger():
    _logger.remove()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    _logger.add(sys.stderr, format=log_format, level="DEBUG", colorize=True)
    return _logger


logger = setup_logger()
