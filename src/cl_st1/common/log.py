# Python
import logging
from typing import Optional


def get_logger(name: str = "cl_st1", level: int = logging.INFO, logfile: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    if logfile:
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger