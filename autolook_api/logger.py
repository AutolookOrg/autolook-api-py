from dataclasses import dataclass
from typing import Optional
import colorlog
import logging
from logging import Logger

def setup_colored_logger(name: str = None) -> Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s %(levelname)-8s %(reset)s : %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'blue',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

@dataclass
class _Colors:
    CYAN: str
    GREEN: str
    YELLOW: str
    RED: str
    MAGENTA: str
    RESET: str
COLORS = _Colors(
    CYAN='\033[36m', # Cyan
    GREEN='\033[32m', # Green
    YELLOW='\033[33m', # Yellow
    RED='\033[31m', # Red
    MAGENTA='\033[35m', # Magenta
    RESET='\033[0m' # Reset
)

_LOGGER: Optional[Logger] = None
def l() -> Logger:
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = setup_colored_logger("AL_LOGGER")
    return _LOGGER
